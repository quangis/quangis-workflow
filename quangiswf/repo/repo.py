from rdflib.term import Node, URIRef, BNode
from rdflib import Graph
from typing import Iterator
from transforge.list import GraphList
from itertools import count
from collections import defaultdict

from quangiswf.namespace import (bind_all, TOOLSCHEMA, DATA, RDF, WF, CCT_)
from quangiswf.repo.workflow import Workflow
from quangiswf.repo.tool import (Implementation, ToolRepo, Supertool, 
    ToolNotFoundError)
from quangiswf.repo.signature import (SignatureRepo, Signature, 
    SignatureNotFoundError)

class Repo(object):
    """A repository contains signatures and tools."""

    def __init__(self) -> None:
        self.signatures = SignatureRepo()
        self.tools = ToolRepo()
        super().__init__()

    def signed_actions(self, wf: Workflow, root: Node) \
            -> Iterator[tuple[Node, URIRef | Supertool, Signature]]:
        assert (root, RDF.type, WF.Workflow) in wf

        for action in wf.high_level_actions(root):
            _, impl = wf.impl(action)
            try:
                proposal_sig = Signature.propose(wf, action)
                if isinstance(impl, BNode):
                    proposal_tool = Supertool.propose(wf, action)
                    tool = self.tools.find_tool(proposal_tool)
                else:
                    assert isinstance(impl, URIRef)
                    tool = self.tools.tools[impl].uri
                proposal_sig.implementations.add(tool)
                sig = self.signatures.find_signature(proposal_sig)
            except SignatureNotFoundError:
                if impl and (impl, RDF.type, WF.Workflow) in wf:
                    yield from self.signed_actions(wf, impl)
                else:
                    raise
            yield action, tool, sig

    def convert_to_signatures(self, wf: Workflow, root: Node) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only signatures."""

        g = GraphList()
        g.base = DATA
        bind_all(g, default=TOOLSCHEMA)

        assert (root, RDF.type, WF.Workflow) in wf
        g.add((root, RDF.type, WF.Workflow))

        counter = count()
        map: dict[Node, BNode] = defaultdict(
            lambda: BNode(f"out{next(counter)}"))

        inputs, outputs = wf.io(root)
        for i, artefact in enumerate(inputs, start=1):
            map[artefact] = BNode(f"in{i}")
            g.add((root, WF.source, map[artefact]))
        for artefact in outputs:
            g.add((root, WF.target, map[artefact]))

        for orig_action, tool, sig in self.signed_actions(wf, root):
            assert sig.uri
            action = BNode()
            g.add((root, WF.edge, action))
            g.add((action, WF.applicationOf, sig.uri))
            for i, artefact in enumerate(
                    wf.inputs(orig_action, labelled=True), start=1):
                g.add((action, WF[f"input{i}"], map[artefact]))
            for pred, artefact in zip([WF.output], wf.outputs(orig_action)):
                g.add((action, pred, map[artefact]))

        return g

    def update_action(self, wf: Workflow, action: Node) -> None:
        """Analyze a single action (application of a tool or workflow) and 
        figure out the (super)tool it uses, as well as the signature it belongs 
        to. Both will be created, if necessary. This must be done in tandem, 
        because a supertool need only be created when there's a signature with 
        which to associate it."""

        # Propose the tool and signature that would be created if no other 
        # tools or supertools existed in the repository yet
        proposal_sig = Signature.propose(wf, action)
        _, impl = wf.impl(action)
        proposal_imp: Implementation
        if isinstance(impl, URIRef):
            proposal_imp = self.tools.tools[impl]
        else:
            proposal_imp = Supertool.propose(wf, action)
        try:
            impl_uri = self.tools.find_tool(proposal_imp)
        except ToolNotFoundError:
            assert isinstance(proposal_imp, Supertool)
            impl_uri = self.tools.register_supertool(proposal_imp).uri
        proposal_sig.implementations.add(impl_uri)

        # Find out how existing signatures relate to the proposed sig
        supersig: Signature | None = None
        subsigs: list[Signature] = []
        for uri, sig in self.signatures.signatures.items():
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

        # If the signature is a more general version of existing signature(s), 
        # then we must update the outdated specs.
        elif subsigs:
            assert len(subsigs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            subsigs[0].inputs = proposal_sig.inputs
            subsigs[0].outputs = proposal_sig.outputs

        # If neither is the case, the action merits an all-new signature
        else:
            self.signatures.register_signature(proposal_sig)

    def update(self, wf: Workflow):
        for action, impl in wf.subject_objects(WF.applicationOf):
            if wf.value(action, CCT_.expression):
                self.update_action(wf, action)

    def graph(self) -> Graph:
        return self.tools.graph() + self.signatures.graph()
