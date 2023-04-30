from __future__ import annotations
from rdflib import Graph
from rdflib.term import Node, URIRef, BNode, Literal
from transforge.list import GraphList
from transforge.namespace import shorten
from itertools import chain, count

from quangis_workflows.types import Polytype
from quangis_workflows.repo.workflow import Workflow
from quangis_workflows.repo.tool import ToolRepo, Supertool, ToolNotFoundError
from quangis_workflows.namespace import (
    bind_all, n3, SIG, CCT, RDF, WF, TOOL, DATA)
from cct import cct
from typing import Iterator

cctlang = cct


class SignatureNotFoundError(Exception):
    pass


class Signature(object):
    """A tool signature is an abstract specification of a tool. It may 
    correspond to one or more concrete tools, or even ensembles of tools. It 
    must describe the format of its input and output (ie the core concept 
    datatypes) and it may describe its purpose (in terms of a core concept 
    transformation expression).

    A signature may be implemented by multiple (super)tools, because, for 
    example, a tool could be implemented in both QGIS and ArcGIS. Conversely, 
    multiple signatures may be implemented by the same (super)tool, if it can 
    be used in multiple contexts --- in the same way that a hammer can be used 
    either to drive a nail into a plank of wood or to break a piggy bank."""

    def __init__(self,
            inputs: list[Polytype],
            outputs: list[Polytype],
            cct: str | None,
            impl: URIRef | None = None) -> None:
        self.inputs: list[Polytype] = inputs
        self.outputs: list[Polytype] = outputs
        self.cct: str | None = cct
        self.uri: URIRef | None = None
        self.description: str | None = None
        self.implementations: set[URIRef] = set()
        if impl:
            self.implementations.add(impl)

        self.cct_p = cctlang.parse(cct, defaults=True) if cct else None

    @staticmethod
    def propose(wf: Workflow, action: Node) -> Signature:
        """Create a new signature proposal from a tool application."""
        return Signature(
            inputs=[wf.type(artefact) for artefact in wf.inputs(action)],
            outputs=[wf.type(artefact) for artefact in wf.outputs(action)],
            cct=wf.cct(action)
        )

    def covers_implementation(self, candidate: Signature) -> bool:
        return candidate.implementations.issubset(self.implementations)

    def matches_cct(self, candidate: Signature) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return (self.cct_p and candidate.cct_p
            and self.cct_p.match(candidate.cct_p))

    def subsumes_datatype(self, candidate: Signature) -> bool:
        """If the inputs in the candidate signature are subtypes of the ones in 
        this one (and the outputs are supertypes), then this signature *covers* 
        the other signature. If the reverse is true, then this signature is 
        narrower than what the candidate one requires, which suggests that it 
        should be generalized. If the candidate signature is neither covered by 
        this one nor generalizes it, then the two signatures are 
        independent."""

        # For now, we do not take into account permutations. We probably 
        # should, since even in the one test that I did (wffood), we see that 
        # SelectLayerByLocationPointObjects has two variants with just the 
        # order of the inputs flipped.
        il = len(self.inputs)
        ol = len(self.outputs)
        if il != ol:
            return False

        return (
            all(candidate.inputs[k1].subtype(self.inputs[k2])
                for k1, k2 in zip(range(il), range(il)))
            and all(self.outputs[k1].subtype(candidate.outputs[k2])
                for k1, k2 in zip(range(ol), range(ol)))
        )


class SignatureRepo(object):
    """
    A signature repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        # Signatures (abstract tools)
        self.signatures: dict[URIRef, Signature] = dict()

    def __contains__(self, sig: URIRef) -> bool:
        return sig in self.signatures

    def generate_name(self, base: str) -> URIRef:
        """
        Generate a name for a signature based on an existing concrete tool.
        """
        for i in chain([""], count(start=2)):
            uri = SIG[f"{base}{i}"]
            if uri not in self:
                return uri
        raise RuntimeError("Unreachable")

    def find_signature(self, proposal: Signature) -> Signature:
        """Find a signature that matches the proposed signature."""
        for sig in self.signatures.values():
            if (sig.covers_implementation(proposal)
                    and sig.subsumes_datatype(proposal)
                    and sig.matches_cct(proposal)):
                return sig

        sigs: set[Node] = set(s.uri for s in self.signatures.values()
            if s.covers_implementation(proposal) if s.uri)
        raise SignatureNotFoundError(
            f"The repository contains no signature for an application of "
            f"{'/'.join(n3(impl) for impl in proposal.implementations)}. "
            f"The following signatures exist for other applications of this "
            f"tool: {n3(sigs)}")

    def signed_actions(self, wf: Workflow, root: Node, tools: ToolRepo) \
            -> Iterator[tuple[Node, URIRef | Supertool, Signature]]:
        assert (root, RDF.type, WF.Workflow) in wf

        for action in wf.high_level_actions(root):
            try:
                proposal_sig = Signature.propose(wf, action)
                if not proposal_sig.cct:
                    raise SignatureNotFoundError(
                        f"The signature for workflow {n3(root)} has no "
                        f"CCT expression associated with it.")
                proposal_tool = Supertool.propose(wf, action)
                tool = tools.find_tool(proposal_tool)
                proposal_sig.implementations.add(tool)
                sig = self.find_signature(proposal_sig)
            except SignatureNotFoundError:
                impl = wf.value(action, WF.applicationOf, any=False)
                if impl and (impl, RDF.type, WF.Workflow) in wf:
                    yield from self.signed_actions(wf, impl, tools)
                else:
                    raise
            yield action, tool, sig

    def convert_to_signatures(self, wf: Workflow, root: Node,
            tools: ToolRepo) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only signatures."""

        g = GraphList()
        g.base = DATA
        bind_all(g, default=TOOL)

        assert (root, RDF.type, WF.Workflow) in wf
        g.add((root, RDF.type, WF.Workflow))

        inputs, outputs = wf.io(root)
        for artefact in inputs:
            g.add((root, WF.source, artefact))
        for artefact in outputs:
            g.add((root, WF.target, artefact))

        for action, tool, sig in self.signed_actions(wf, root, tools):
            assert sig.uri
            g.add((root, WF.edge, action))
            g.add((action, WF.applicationOf, sig.uri))
            for i, artefact in enumerate(wf.inputs(action), start=1):
                g.add((action, WF[f"input{i}"], artefact))
            for pred, artefact in zip([WF.output], wf.outputs(action)):
                g.add((action, pred, artefact))

        return g

    def analyze_action(self, wf: Workflow,
            action: Node, tools: ToolRepo) -> URIRef | None:
        """Analyze a single action (application of a tool or workflow) and 
        figure out the (super)tool it uses, as well as the signature it belongs 
        to. Both will be created, if necessary. This must be done in tandem, 
        because a supertool need only be created when there's a signature with 
        which to associate it."""

        impl_orig = wf.value(action, WF.applicationOf, any=False)
        assert impl_orig

        proposal_sig = Signature.propose(wf, action)
        if not proposal_sig.cct:
            # print(f"Skipping an application of {n3(impl_orig)} because it "
            #     f"has no CCT expression.""")
            return None

        proposal_imp = Supertool.propose(wf, action)
        try:
            impl_uri = tools.find_tool(proposal_imp)
        except ToolNotFoundError:
            assert isinstance(proposal_imp, Supertool)
            impl_uri = tools.register_supertool(proposal_imp).uri

        # TODO: Finding the signature should be done differently for a workflow 
        # than for a concrete tool, because we can work off different 
        # assumptions. Do so later.

        # Find out how other signatures relate to the candidate sig
        supersig: Signature | None = None
        subsigs: list[Signature] = []
        for uri, sig in self.signatures.items():
            # Is the URI the same?
            if impl_uri not in sig.implementations:
                continue

            # Is the CCT expression the same?
            if not proposal_sig.matches_cct(sig):
                continue

            # Is the CCD type the same?
            if proposal_sig.subsumes_datatype(sig):
                assert not supersig
                supersig = sig
            elif sig.subsumes_datatype(proposal_sig):
                subsigs.append(sig)

        assert not (supersig and subsigs), """If this assertion fails, the tool 
        repository already contains too many specs."""

        # If there is a signature that covers this action, we simply add the 
        # corresponding tool/workflow as one of its implementations
        if supersig:
            supersig.implementations.add(impl_uri)
            return supersig.uri

        # If the signature is a more general version of existing signature(s), 
        # then we must update the outdated specs.
        elif subsigs:
            assert len(subsigs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            subsigs[0].inputs = proposal_sig.inputs
            subsigs[0].outputs = proposal_sig.outputs
            return subsigs[0].uri

        # If neither of the above is true, the action merits an all-new spec
        else:
            proposal_sig.uri = self.generate_name(shorten(impl_orig))
            self.signatures[proposal_sig.uri] = proposal_sig
            return proposal_sig.uri

    def collect(self, wf: Workflow, tools: ToolRepo):
        for action, impl in wf.subject_objects(WF.applicationOf):
            self.analyze_action(wf, action, tools)

    def graph(self) -> Graph:
        g = GraphList()
        bind_all(g, TOOL)

        for sig in self.signatures.values():
            assert isinstance(sig.uri, URIRef)

            g.add((sig.uri, RDF.type, TOOL.Signature))
            g.add((sig.uri, CCT.expression, Literal(sig.cct)))

            for impl in sig.implementations:
                g.add((sig.uri, TOOL.implementation, impl))
                g.add((impl, TOOL.signature, sig.uri))

            inputs = []
            for i in range(len(sig.inputs)):
                artefact = BNode()
                for uri in sig.inputs[i].uris():
                    g.add((artefact, RDF.type, uri))
                inputs.append(artefact)
            g.add((sig.uri, TOOL.inputs, g.add_list(inputs)))

            outputs = []
            for i in range(len(sig.outputs)):
                artefact = BNode()
                for uri in sig.outputs[i].uris():
                    g.add((artefact, RDF.type, uri))
                outputs.append(artefact)
            g.add((sig.uri, TOOL.outputs, g.add_list(outputs)))

        return g
