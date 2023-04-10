#!/usr/bin/env python3
"""
This module is work-in-progerss. It does two things:

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
from rdflib.term import Node, BNode, URIRef, Literal
from pathlib import Path
from itertools import count
from random import choices
import string
from typing import Iterator, Sequence
from collections import defaultdict

from cct import cct  # type: ignore
import transforge as tf
from transforge.namespace import shorten
from quangis_workflows.namespace import n3, WF, RDF, CCD, CCT, TOOLS
from quangis_workflows.types import Polytype, Dimension

root_dir = Path(__file__).parent.parent
type_graph = Graph()
type_graph.parse(root_dir / "CoreConceptData.rdf", format="xml")

dimensions = [
    Dimension(root, type_graph)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]


class GraphList(Graph):
    """
    An RDF graph augmented with methods for creating, reading and destroying 
    lists.
    """

    def __init__(self) -> None:
        super().__init__()

    def add_list(self, items: Sequence[Node]) -> Node:
        if not items:
            return RDF.nil
        node = BNode()
        self.add((node, RDF.first, items[0]))
        self.add((node, RDF.rest, self.add_list(items[1:])))
        return node

    def get_list(self, list_node: Node) -> Iterator[Node]:
        node: Node | None = list_node
        while first := self.value(node, RDF.first, any=False):
            yield first
            node = self.value(node, RDF.rest, any=False)
        if not node == RDF.nil:
            raise RuntimeError("Node is not an RDF list")

    def remove_list(self, list_node: Node) -> None:
        next_node = self.value(list_node, RDF.rest, any=False)
        if next_node:
            self.remove_list(next_node)
        self.remove((list_node, RDF.first, None))
        self.remove((list_node, RDF.rest, None))


Spec = URIRef
Tool = URIRef


class ToolRepository(object):
    """
    A tool repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        self._implementations: dict[Spec, set[Tool]] = defaultdict(set)

        # Map abstract tools to input and output types
        self._sig_in: dict[Spec, list[Polytype]] = {}
        self._sig_out: dict[Spec, list[Polytype]] = {}
        self._sig_sem: dict[Spec, tf.Expr] = {}

    def __contains__(self, spec: Spec) -> bool:
        return spec in self._implementations

    def generate_name(self, base: Tool) -> Spec:
        """
        Generate a name for an abstract tool based on an existing concrete 
        tool.
        """
        id = "".join(choices(string.ascii_letters + string.digits, k=5))
        name = TOOLS[f"{shorten(base)}_{id}"]
        if name in self:
            return self.generate_name(base)
        return name

    def analyze_action(self, wf: ConcreteWorkflow, action: Node) -> Spec:
        """
        Analyze a single action (application of a tool) and figure out what 
        spec it belongs to. As a side-effect, update the repository of tool 
        specifications if necessary.
        """
        tool = wf.tool(action)
        action_sig_in = wf.sig_in(action)
        action_sig_out = wf.sig_out(action)
        # action_sig_sem = wf.sig_sem(action)

        # Now there are three possibilities:
        # - there is already a "super"spec that covers this action;
        # - this action suggests that one or more existing "sub"specs need to 
        # be generalized to fit it;
        # - this action merits an all-new spec.

        superspec: Spec | None = None
        subspecs: list[Spec] = []

        for candidate_spec in self._implementations:
            # Is the URI the same?
            if tool not in self._implementations[candidate_spec]:
                continue

            # Is the CCT term the same?
            # if not self._sig_sem[candidate_spec].match(action_sig_sem):
                # TODO Note that non-matching CCT doesn't mean that tools are 
                # actually semantically different. Some degree of manual 
                # intervention might be necessary.
                # continue

            # As for the CCD signature: if the inputs of the action are a 
            # supertype of those in the spec (and the outputs are a subtype), 
            # then the action is more general than the spec. Other way around, 
            # it is more specific. (If both are true, the spec matches the 
            # action; if neither are true, then they are independent.)
            spec_sig_in = self._sig_in[candidate_spec]
            spec_sig_out = self._sig_out[candidate_spec]
            specCoversAction = (
                all(t_action.subtype(t_spec)
                    for t_action, t_spec in zip(action_sig_in, spec_sig_in))
                and all(t_spec.subtype(t_action)
                    for t_action, t_spec in zip(action_sig_out, spec_sig_out))
            )
            actionGeneralizesSpec = (
                all(t_spec.subtype(t_action)
                    for t_action, t_spec in zip(action_sig_in, spec_sig_in))
                and all(t_action.subtype(t_spec)
                    for t_action, t_spec in zip(action_sig_out, spec_sig_out))
            )

            # TODO Do we take into account permutations of the inputs?

            if specCoversAction:
                assert not superspec
                superspec = candidate_spec
            elif actionGeneralizesSpec:
                subspecs.append(candidate_spec)

        assert not (superspec and subspecs), """If this assertion fails, the 
        tool repository already contains too many specs."""

        spec: Spec

        # If there is a spec that covers this action, we simply add the 
        # corresponding tool/workflow as one of its implementations
        if superspec:
            spec = superspec
            self._implementations[superspec].add(tool)

        # If the action is a more general version of existing spec(s), then we 
        # must update the outdated specs.
        elif subspecs:
            assert len(subspecs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            spec = subspecs[0]
            self._sig_in[spec] = action_sig_in
            self._sig_out[spec] = action_sig_out

        # If neither of the above is true, the action merits an all-new spec
        else:
            spec = self.generate_name(tool)
            self._implementations[spec].add(tool)
            self._sig_in[spec] = action_sig_in
            self._sig_out[spec] = action_sig_out
            # self._sig_sem[spec] = action_sig_sem

        return spec

    def collect(self, wf: ConcreteWorkflow):
        for action, tool in wf.subject_objects(WF.applicationOf):
            print(f"Analyzing an application of {n3(tool)}:")
            spec = self.analyze_action(wf, action)
            print(f"Part of {spec}")
        print(self.graph().serialize(format="turtle"))

    def graph(self) -> ToolRepositoryGraph:
        return ToolRepositoryGraph(self)


class ToolRepositoryGraph(GraphList):

    def __init__(self, repo: ToolRepository) -> None:
        super().__init__()

        self.bind("", TOOLS)
        self.bind("ccd", CCD)

        for spec, implementations in repo._implementations.items():
            for impl in implementations:
                self.add((spec, TOOLS.implementedBy, impl))

        for spec, sig in repo._sig_in.items():
            self.add((spec, TOOLS.input,
                self.add_list([self.add_artefact(t) for t in sig])))

        for spec, sig in repo._sig_out.items():
            self.add((spec, TOOLS.output,
                self.add_list([self.add_artefact(t) for t in sig])))

        for spec, expr in repo._sig_sem.items():
            self.add((spec, CCT.expression, Literal(str(expr))))

    def add_artefact(self, type: Polytype) -> Node:
        artefact = BNode()
        for uri in type.uris():
            self.add((artefact, RDF.type, uri))
        return artefact

    def remove_spec(self, spec: URIRef):
        self.remove((spec, CCT.expression, None))
        for predicate in (TOOLS.input, TOOLS.output):
            for artefact_list in self.objects(spec, predicate):
                for artefact in self.get_list(artefact_list):
                    self.remove((artefact, RDF.type, None))
                self.remove_list(artefact_list)


class ConcreteWorkflow(Graph):
    def __init__(self, root: URIRef, *nargs, **kwargs):
        self.root = root
        super().__init__(*nargs, **kwargs)

    def type(self, artefact: Node) -> Polytype:
        return Polytype.assemble(dimensions, self.objects(artefact, RDF.type))

    def sig_sem(self, action: Node) -> tf.Expr:
        expr_string = self.value(action, CCT.expression, any=False)
        return cct.parse(expr_string, defaults=True)

    def tool(self, action: Node) -> URIRef:
        tool = self.value(action, WF.applicationOf, any=False)
        assert isinstance(tool, URIRef)
        return tool

    def sig_out(self, action: Node) -> list[Polytype]:
        artefact_out = self.value(action, WF.output, any=False)
        assert artefact_out
        return [self.type(artefact_out)]

    def sig_in(self, action: Node) -> list[Polytype]:
        result = []
        for i in count(start=1):
            artefact_in = self.value(action, WF[f"input{i}"], any=False)
            if not artefact_in:
                break
            result.append(self.type(artefact_in))
        return result

    @staticmethod
    def from_file(path: str | Path, root: URIRef) -> ConcreteWorkflow:
        g = ConcreteWorkflow(root)
        g.parse(path, format="turtle")
        return g


if __name__ == "__main__":
    cwf = ConcreteWorkflow.from_file(
        root_dir / "wffood.ttl", TOOLS.wfcrime_route)
    repo = ToolRepository()
    repo.collect(cwf)
