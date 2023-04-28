#!/usr/bin/env python3
"""
This module is work-in-progress. It does two things:

-   It collects *abstract tools* from *concrete workflows*.
-   It turns the *concrete workflow* into abstract.

A concrete workflow is a graph that consists solely of actions (*applications* 
of tool implementations), along with CCT-terms that express their 
functionality, plus artefacts (their concrete inputs and outputs), along with 
CCD annotations.

Additionally, in the case that a single tool cannot be expressed meaningfully 
with a CCT-term, the graph may include ad-hoc "supertool" applications, which 
point to an *ensemble* of tool applications that can be given a term 
collectively.

There is an existing store for abstract tools. This acts as validation for 
every additional tool and it should also avoid duplication. It should 
recognize:
-   when a tool with the same signature is already in the store;
-   when a tool is already in the store with a signature of a CCD subtype;
-   when a tool is already in the store with a different order to the inputs;

Furthermore, we could check consistency between CCD's semantic dimension and 
CCT types.
"""

from __future__ import annotations

import re
import random
import string
from rdflib import Graph
from rdflib.compare import isomorphic
from rdflib.term import Node, BNode, URIRef, Literal
from rdflib.util import guess_format
from pathlib import Path
from itertools import count, chain
from collections import defaultdict
from typing import Iterator, Iterable

from cct import cct  # type: ignore
from transforge.namespace import shorten
from quangis_workflows.namespace import (
    WF, RDF, CCD, CCT, CCT_, TOOLS, TOOL, DATA, OWL, SUPERTOOL, SIG, ARC, n3, 
    namespaces)
from quangis_workflows.types import Polytype, Dimension
from quangis_workflows.tool2url import tool2url

from transforge.list import GraphList

cctlang = cct

root_dir = Path(__file__).parent.parent
type_graph = Graph()
type_graph.parse(root_dir / "CoreConceptData.rdf", format="xml")

dimensions = [
    Dimension(root, type_graph)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]


class NoSignatureError(Exception):
    pass


class EmptyTransformationError(Exception):
    pass


class Action(object):
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


class RepoSignatures(object):
    """
    A signature repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        # Signatures (abstract tools)
        self.signatures: dict[URIRef, Signature] = dict()

        # Ensembles of concrete tools (workflow schemas)
        self.tools = RepoTools()

    @staticmethod
    def from_file(self) -> RepoSignatures:
        raise NotImplementedError

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

    def find(self, proposal: Signature) -> Signature:
        """Find a signature that matches the proposed signature."""
        for sig in self.signatures.values():
            if (sig.covers_implementation(proposal)
                    and sig.subsumes_datatype(proposal)
                    and sig.matches_cct(proposal)):
                return sig

        sigs = set(s.uri for s in self.signatures.values()
            if s.covers_implementation(proposal))
        raise NoSignatureError(f"The repository contains no matching "
            f"signature for an application of {n3(proposal.implementations)}. "
            f"The following signatures do exist for this tool: "
            f"{n3(sigs)}")

    def analyze_action(self, wf: ConcreteWorkflow,
            action: Node) -> URIRef | None:
        """
        Analyze a single action (application of a tool or workflow) and figure 
        out what spec it belongs to. As a side-effect, update the repository of 
        tool specifications if necessary.
        """

        impl_orig = wf.value(action, WF.applicationOf, any=False)
        assert impl_orig

        candidate = wf.signature(action)
        if not candidate.cct:
            print(f"Skipping an application of {n3(impl_orig)} because it "
                f"has no CCT expression.""")
            return None

        impl = self.tools.find_tool(wf, action)

        # TODO: Finding the signature should be done differently for a workflow 
        # than for a concrete tool, because we can work off different 
        # assumptions. Do so later.

        # Find out how other signatures relate to the candidate sig
        supersig: Signature | None = None
        subsigs: list[Signature] = []
        for uri, sig in self.signatures.items():
            # Is the URI the same?
            if impl not in sig.implementations:
                continue

            # Is the CCT expression the same?
            if not candidate.matches_cct(sig):
                continue

            # Is the CCD type the same?
            if candidate.subsumes_datatype(sig):
                assert not supersig
                supersig = sig
            elif sig.subsumes_datatype(candidate):
                subsigs.append(sig)

        assert not (supersig and subsigs), """If this assertion fails, the tool 
        repository already contains too many specs."""

        # If there is a signature that covers this action, we simply add the 
        # corresponding tool/workflow as one of its implementations
        if supersig:
            supersig.implementations.add(impl)
            return supersig.uri

        # If the signature is a more general version of existing signature(s), 
        # then we must update the outdated specs.
        elif subsigs:
            assert len(subsigs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            subsigs[0].inputs = candidate.inputs
            subsigs[0].outputs = candidate.outputs
            return subsigs[0].uri

        # If neither of the above is true, the action merits an all-new spec
        else:
            candidate.uri = self.generate_name(shorten(impl))
            self.signatures[candidate.uri] = candidate
            return candidate.uri

    def collect(self, wf: ConcreteWorkflow):
        for action, impl in wf.subject_objects(WF.applicationOf):
            self.analyze_action(wf, action)

    def graph(self) -> Graph:
        g = GraphList()
        g.bind("", TOOL)
        g.bind("tools", TOOLS)
        g.bind("sig", SIG)
        g.bind("supertool", SUPERTOOL)
        g.bind("ccd", CCD)
        g.bind("cct_", CCT_)
        g.bind("cct", CCT)
        g.bind("data", DATA)
        g.bind("arc", ARC)

        for sig in self.signatures.values():
            assert isinstance(sig.uri, URIRef)

            g.add((sig.uri, RDF.type, TOOL.Signature))

            for impl in sig.implementations:
                g.add((sig.uri, TOOL.implementation, impl))
                if impl in self.tools.supertools:
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

            g.add((sig.uri, CCT.expression, Literal(sig.cct)))

        for tool, wf in self.tools.supertools.items():
            g += wf

        return g


class ConcreteWorkflow(Graph):
    """
    Concrete workflow in old format.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self._root: Node | None = None
        super().__init__(*nargs, **kwargs)

    def signature(self, action: Node) -> Signature:
        """Create a new signature proposal from an action in a workflow."""
        return Signature(
            inputs=[self.type(artefact) for artefact in self.inputs(action)],
            outputs=[self.type(artefact) for artefact in self.outputs(action)],
            cct=self.cct(action),
            impl=self.implementation(action)[1]
        )

    def type(self, artefact: Node) -> Polytype:
        return Polytype.assemble(dimensions, self.objects(artefact, RDF.type))

    @property
    def root(self) -> Node:
        if not self._root:
            self._root = self.find_root()
        return self._root

    def find_root(self) -> Node:
        # To find the root of a workflow, find a Workflow that isn't used as an 
        # action anywhere; or, if it is, at least make sure that that action 
        # isn't a step of any other Workflow.

        for wf in self.subjects(RDF.type, WF.Workflow):
            action_in_other_workflow: Node | None = None

            for action in self.subjects(WF.applicationOf, wf):
                if self.value(None, WF.edge, action):
                    action_in_other_workflow = action
                    break

            if not action_in_other_workflow:
                return wf
        raise RuntimeError("Workflow graph has no identifiable root.")

    def cct(self, action: Node) -> str | None:
        a = (self.value(action, CCT_.expression, any=False) or
            self.value(action, CCT.expression, any=False))
        if isinstance(a, Literal):
            return str(a)
        elif not a:
            return None
        raise RuntimeError("Core concept transformation must be literal")

    def implementation(self, action: Node) -> tuple[str, URIRef]:
        impl = self.value(action, WF.applicationOf, any=False)
        assert isinstance(impl, URIRef)
        name = shorten(impl)

        if (impl, RDF.type, WF.Workflow) in self:
            return name, SUPERTOOL[name]
        else:
            return name, URIRef(tool2url[name])

    def inputs(self, action: Node) -> Iterator[Node]:
        for i in count(start=1):
            artefact = self.value(action, WF[f"input{i}"], any=False)
            if artefact:
                yield artefact
            else:
                break

    def outputs(self, action: Node) -> Iterator[Node]:
        artefact_out = self.value(action, WF.output, any=False)
        assert artefact_out
        yield artefact_out

    def extremities(self, wf: Node) -> tuple[set[Node], set[Node]]:
        """
        Find the inputs and outputs of a workflow by looking at which inputs 
        and outputs of the actions aren't themselves given to or from other 
        actions.
        """
        assert (wf, RDF.type, WF.Workflow) in self

        inputs: set[Node] = set()
        outputs: set[Node] = set()
        for action in self.objects(wf, WF.edge):
            inputs.update(self.inputs(action))
            outputs.update(self.outputs(action))
        ginputs = inputs - outputs
        goutputs = outputs - inputs

        # Sanity check
        gsources = set(self.objects(wf, WF.source))
        assert gsources == ginputs, f"""The sources of the workflow {n3(wf)}, 
        namely {n3(gsources)}, don't match with the inputs {n3(ginputs)}."""

        return ginputs, goutputs

    @staticmethod
    def from_file(path: str | Path, format: str = "") -> ConcreteWorkflow:
        g = ConcreteWorkflow()
        g.parse(path, format=format or guess_format(str(path)))
        return g

    def high_level_actions(self, root: Node) -> Iterator[Node]:
        assert (root, RDF.type, WF.Workflow) in self
        for action in self.objects(root, WF.edge):
            if tuple(self.subjects(WF.edge, action)) == (root,):
                yield action

    def low_level_actions(self, root: Node) -> Iterator[Node]:
        assert (root, RDF.type, WF.Workflow) in self
        for action in self.objects(root, WF.edge):
            impl = self.value(action, WF.applicationOf, any=False)
            if impl == root:
                continue
            elif impl and (impl, WF.edge, None) in self:
                yield from self.low_level_actions(impl)
            else:
                yield action

    def signed_actions(self, root: Node,
            repo: RepoSignatures) -> Iterator[tuple[Node, Signature]]:
        assert (root, RDF.type, WF.Workflow) in self
        for action in self.high_level_actions(root):
            try:
                action_sig = self.signature(action)
                sig = repo.find(action_sig)
            except NoSignatureError:
                impl = self.value(action, WF.applicationOf, any=False)
                if impl and (impl, RDF.type, WF.Workflow) in self:
                    yield from self.signed_actions(impl, repo)
                else:
                    raise
            yield action, sig

    def abstraction(self, wf: Node, repo: RepoSignatures, root: Node = None,
            base: tuple[GraphList, dict[Node, Node]] | None = None) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only signatures."""

        g, map = base or (GraphList(), defaultdict(BNode))
        root = root or wf

        if not base:
            g.base = DATA
            g.bind("", TOOL)
            for prefix, ns in namespaces.items():
                if prefix != "tool":
                    g.bind(prefix, ns)

        assert (wf, RDF.type, WF.Workflow) in self
        g.add((root, RDF.type, WF.Workflow))

        if wf == root:
            inputs, outputs = self.extremities(wf)
            for pred, artefacts in ((WF.source, inputs), (WF.target, outputs)):
                for artefact in artefacts:
                    g.add((wf, pred, artefact))

        for action, sig in self.signed_actions(wf, repo):
            # assert (action, CCT.expression, None) in self
            g.add((root, WF.edge, map[action]))
            g.add((map[action], WF.applicationOf, sig.uri))

            for i, artefact in enumerate(self.inputs(action), start=1):
                g.add((map[action], WF[f"input{i}"], artefact))

            for pred, artefact in zip([WF.output], self.outputs(action)):
                g.add((map[action], pred, artefact))

        return g

    def tool(self, action: Node) -> URIRef:
        """Assuming that the action represents an application of a concrete 
        tool, return the link to that tool."""
        uri = self.value(action, WF.applicationOf, any=False)
        assert isinstance(uri, URIRef)
        assert (uri, RDF.type, WF.Workflow) not in self
        return URIRef(tool2url[shorten(uri)])


class RepoTools(object):
    # TODO input/output permutations

    tools = tool2url

    def __init__(self) -> None:
        self.supertools: dict[URIRef, Supertool] = dict()

    def find_tool(self, wf: ConcreteWorkflow, action: Node) -> URIRef:
        """Find an implementation that matches this action. This is an 
        expensive operation because, in the case of a supertool, a proposal 
        supertool is extracted and checked for isomorphism with existing 
        supertools."""
        impl = wf.value(action, WF.applicationOf, any=False)
        assert impl
        name = shorten(impl)

        if (impl, RDF.type, WF.Workflow) in wf:
            supertool = Supertool(SUPERTOOL[name],
                inputs=wf.inputs(action),
                outputs=wf.outputs(action),
                actions=((wf.tool(sub), wf.inputs(sub), wf.outputs(sub))
                    for sub in wf.low_level_actions(impl)))
            supertool = (self.find_supertool(supertool)
                or self.register_supertool(supertool))
            return supertool.uri
        else:
            return URIRef(tool2url[name])

    def find_supertool(self, supertool: Supertool) -> Supertool | None:
        """Find a supertool even if the name doesn't match."""

        if (supertool.uri in self.supertools):
            if supertool.match(self.supertools[supertool.uri]):
                return self.supertools[supertool.uri]
            else:
                raise RuntimeError(f"{n3(supertool.uri)} is in repo but "
                    f"doesn't match the given supertool of the same name.")

        for st in self.supertools.values():
            if supertool.match(st):
                return st

        return None

    def register_supertool(self, supertool: Supertool) -> Supertool:
        supertool.sanity_check()
        if (supertool.uri in self.supertools and not
                supertool.match(self.supertools[supertool.uri])):
            raise RuntimeError
        self.supertools[supertool.uri] = supertool
        return supertool


class Supertool(GraphList):
    """A supertool is a workflow schema."""

    def __init__(self, uri: URIRef,
            inputs: Iterable[Node], outputs: Iterable[Node],
            actions: Iterable[tuple[URIRef, Iterable[Node], Iterable[Node]]]):

        super().__init__()

        code = ''.join(random.choice(string.ascii_lowercase) for i in range(4))

        map: dict[Node, BNode] = defaultdict(
            lambda counter=count(): BNode(f"{code}{next(counter)}"))

        self.uri = uri
        self.inputs = [map[x] for x in inputs]
        self.outputs = [map[x] for x in outputs]
        self.all_inputs: set[BNode] = set()
        self.all_outputs: set[BNode] = set()
        self.tools: set[URIRef] = set()

        self.add((uri, RDF.type, TOOL.Supertool))
        self.add((uri, TOOL.inputs, self.add_list(self.inputs)))
        self.add((uri, TOOL.outputs, self.add_list(self.outputs)))
        for tool, inputs, outputs in actions:
            self._add_action(tool,
                [map[x] for x in inputs],
                [map[x] for x in outputs])

    def _add_action(self, tool: URIRef,
           inputs: Iterable[BNode], outputs: Iterable[BNode]) -> None:
        inputs = inputs if isinstance(inputs, list) else list(inputs)
        outputs = outputs if isinstance(outputs, list) else list(outputs)
        self.all_inputs.update(inputs)
        self.all_outputs.update(outputs)

        action = BNode()
        self.tools.add(tool)
        self.add((self.uri, TOOL.action, action))
        self.add((action, TOOL.apply, tool))
        self.add((action, TOOL.inputs, self.add_list(inputs)))
        self.add((action, TOOL.outputs, self.add_list(outputs)))

    def match(self, other: Supertool) -> bool:
        return other.tools == self.tools and isomorphic(self, other)

    def sanity_check(self):
        """Sanity check."""
        in1 = self.all_inputs - self.all_outputs
        in2 = set(self.inputs)
        out1 = self.all_outputs - self.all_inputs
        out2 = set(self.outputs)
        if not (in1 == in2 and out1 == out2):
            raise RuntimeError(f"In supertool {n3(self.uri)}, there are "
                f"loose inputs or outputs.")
