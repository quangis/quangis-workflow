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

from rdflib import Graph
from rdflib.term import Node, URIRef, Literal
from rdflib.util import guess_format
from pathlib import Path
from itertools import count
from typing import Iterator

from cct import cct  # type: ignore
from transforge.namespace import shorten
from quangis_workflows.namespace import (
    WF, RDF, CCD, CCT, CCT_, TOOL, DATA, SUPERTOOL, n3, bind_all)
from quangis_workflows.types import Polytype, Dimension
from quangis_workflows.tool2url import tool2url
from quangis_workflows.repo.signature import (RepoSignatures,
    Signature, NoSignatureError)
from quangis_workflows.repo.tool import Supertool

from transforge.list import GraphList

cctlang = cct

root_dir = Path(__file__).parent.parent
type_graph = Graph()
type_graph.parse(root_dir / "CoreConceptData.rdf", format="xml")

dimensions = [
    Dimension(root, type_graph)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]


class ConcreteWorkflow(Graph):
    """
    Concrete workflow in old format.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self._root: Node | None = None
        super().__init__(*nargs, **kwargs)

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

    def type(self, artefact: Node) -> Polytype:
        return Polytype.assemble(dimensions, self.objects(artefact, RDF.type))

    def cct(self, action: Node) -> str | None:
        a = (self.value(action, CCT_.expression, any=False) or
            self.value(action, CCT.expression, any=False))
        if isinstance(a, Literal):
            return str(a)
        elif not a:
            return None
        raise RuntimeError("Core concept transformation must be literal")

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

    def io(self, wf: Node) -> tuple[set[Node], set[Node]]:
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
            proposal = self.propose_signature(action)
            try:
                sig = repo.find_signature(proposal)
            except NoSignatureError:
                impl = self.value(action, WF.applicationOf, any=False)
                if impl and (impl, RDF.type, WF.Workflow) in self:
                    yield from self.signed_actions(impl, repo)
                else:
                    raise
            yield action, sig

    def convert_to_signatures(self, root: Node, repo: RepoSignatures) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only signatures."""

        g = GraphList()
        g.base = DATA
        bind_all(g, default=TOOL)

        assert (root, RDF.type, WF.Workflow) in self
        g.add((root, RDF.type, WF.Workflow))

        inputs, outputs = self.io(root)
        for artefact in inputs:
            g.add((root, WF.source, artefact))
        for artefact in outputs:
            g.add((root, WF.target, artefact))

        for action, sig in self.signed_actions(root, repo):
            assert sig.uri
            g.add((root, WF.edge, action))
            g.add((action, WF.applicationOf, sig.uri))
            for i, artefact in enumerate(self.inputs(action), start=1):
                g.add((action, WF[f"input{i}"], artefact))
            for pred, artefact in zip([WF.output], self.outputs(action)):
                g.add((action, pred, artefact))

        return g

    def tool(self, action: Node) -> URIRef:
        """Assuming that the action represents an application of a concrete 
        tool, return the link to that tool."""
        uri = self.value(action, WF.applicationOf, any=False)
        assert isinstance(uri, URIRef)
        assert (uri, RDF.type, WF.Workflow) not in self
        return URIRef(tool2url[shorten(uri)])

    def propose_tool(self, action: Node) -> tuple[str, URIRef | Supertool]:
        """Find an implementation that matches this action. This is an 
        expensive operation because, in the case of a supertool, a proposal 
        supertool is extracted for checking."""
        impl = self.value(action, WF.applicationOf, any=False)
        assert impl
        name = shorten(impl)

        if (impl, RDF.type, WF.Workflow) in self:
            supertool = Supertool(SUPERTOOL[name],
                inputs=self.inputs(action),
                outputs=self.outputs(action),
                actions=((self.tool(sub), self.inputs(sub), self.outputs(sub))
                    for sub in self.low_level_actions(impl)))
            return name, supertool
        else:
            return name, URIRef(tool2url[name])

    def propose_signature(self, action: Node) -> Signature:
        """Create a new signature proposal from an action in a workflow."""
        return Signature(
            inputs=[self.type(artefact) for artefact in self.inputs(action)],
            outputs=[self.type(artefact) for artefact in self.outputs(action)],
            cct=self.cct(action),
            impl=self.tool(action)
        )
