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
from rdflib.term import Node, BNode, URIRef, Literal
from rdflib.util import guess_format
from pathlib import Path
from itertools import count, chain
from random import choices
import string
from typing import Iterator, Sequence
from collections import defaultdict

from cct import cct  # type: ignore
import transforge as tf
from transforge.namespace import shorten
from quangis_workflows.namespace import WF, RDF, CCD, CCT, TOOLS, DATA
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
Impl = URIRef


class ToolRepository(object):
    """
    A tool repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        # Associate specs with the implementations of those specs.
        self._implementations: dict[Spec, set[Impl]] = defaultdict(set)

        # Map specs to input and output signatures.
        self._sig_in: dict[Spec, list[Polytype]] = {}
        self._sig_out: dict[Spec, list[Polytype]] = {}
        self._sig_sem: dict[Spec, tf.Expr] = {}

        # Concrete tool implementations
        self.tools: set[Impl] = set()
        self.schemas: dict[Impl, Graph] = dict()

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

    def analyze_action(self, wf: ConcreteWorkflow,
            action: Node) -> Spec | None:
        """
        Analyze a single action (application of a tool or workflow) and figure 
        out what spec it belongs to. As a side-effect, update the repository of 
        tool specifications if necessary.
        """
        impl = wf.implementation(action)
        action_sig_in = wf.sig_in(action)
        action_sig_out = wf.sig_out(action)
        action_sig_sem = wf.sig_sem(action)

        if not action_sig_sem:
            return None

        # Is this implemented by ensemble of tools or a single concrete tool?
        if (impl, RDF.type, WF.Workflow) in wf:
            if impl not in self.schemas:
                subwf = wf.extract_workflow_schema(impl)
                self.schemas[impl] = subwf
        else:
            self.tools.add(impl)

        # Now there are three possibilities:
        # - there is already a "super"spec that covers this action;
        # - this action suggests that one or more existing "sub"specs need to 
        # be generalized to fit it;
        # - this action merits an all-new spec.

        superspec: Spec | None = None
        subspecs: list[Spec] = []

        for candidate_spec in self._implementations:
            # Is the URI the same?
            if impl not in self._implementations[candidate_spec]:
                continue

            # Is the CCT term the same?
            if not self._sig_sem[candidate_spec].match(action_sig_sem):
                # TODO Note that non-matching CCT doesn't mean that tools are 
                # actually semantically different. Some degree of manual 
                # intervention might be necessary.
                continue

            # As for the CCD signature: if the inputs of the action are a 
            # supertype of those in the spec (and the outputs are a subtype), 
            # then the action is more general than the spec. Other way around, 
            # it is more specific. (If both are true, the spec matches the 
            # action exactly; if neither are true, then they are independent.)
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

            # TODO Do we take into account permutations of the inputs? We 
            # probably should, since even in the one test that I did (wffood), 
            # we see that SelectLayerByLocationPointObjects has two variants 
            # with just the order of the inputs flipped. Actually, it might be 
            # a better idea to identify by ID instead of order.

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
            self._implementations[superspec].add(impl)

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
            spec = self.generate_name(impl)
            self._implementations[spec].add(impl)
            self._sig_in[spec] = action_sig_in
            self._sig_out[spec] = action_sig_out
            self._sig_sem[spec] = action_sig_sem

        return spec

    def collect(self, wf: ConcreteWorkflow):
        for action, impl in wf.subject_objects(WF.applicationOf):
            if action == wf.root:
                continue
            # print(f"Analyzing an application of {n3(impl)}:")
            self.analyze_action(wf, action)
            # print(f"Part of {spec}")
        print(self.graph().serialize(format="turtle"))

    def graph(self) -> ToolRepositoryGraph:
        return ToolRepositoryGraph(self)


class ToolRepositoryGraph(GraphList):

    def __init__(self, repo: ToolRepository) -> None:
        super().__init__()

        self.bind("", TOOLS)
        self.bind("ccd", CCD)
        self.bind("cct", CCT)
        self.bind("data", DATA)

        for spec, implementations in repo._implementations.items():
            for impl in implementations:
                self.add((spec, TOOLS.implementedBy, impl))

        for spec, sig in repo._sig_in.items():
            for i, t in enumerate(sig, start=1):
                a = self.add_artefact(t)
                self.add((spec, TOOLS.input, a))
                self.add((a, TOOLS.id, Literal(i)))

        for spec, sig in repo._sig_out.items():
            for t in sig:
                a = self.add_artefact(t)
                self.add((spec, TOOLS.output, a))

        for spec, expr in repo._sig_sem.items():
            self.add((spec, TOOLS.purpose, Literal(str(expr))))

        for tool in repo.tools:
            self.add((tool, RDF.type, TOOLS.ConcreteTool))

        for tool, wf in repo.schemas.items():
            self += wf

    def add_artefact(self, type: Polytype) -> Node:
        artefact = BNode()
        for uri in type.uris():
            self.add((artefact, RDF.type, uri))
        return artefact


class ConcreteWorkflow(Graph):
    """
    Concrete workflow in old format.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self._root: Node | None = None
        super().__init__(*nargs, **kwargs)

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

    def sig_sem(self, action: Node) -> tf.Expr | None:
        expr_string = self.value(action, CCT.expression, any=False)
        if expr_string:
            return cct.parse(expr_string, defaults=True)
        else:
            return None

    def implementation(self, action: Node) -> URIRef:
        impl = self.value(action, WF.applicationOf, any=False)
        assert isinstance(impl, URIRef)
        return impl

    def inputs(self, action: Node) -> Iterator[Node]:
        for i in count(start=1):
            artefact = self.value(action, WF[f"input{i}"], any=False)
            if artefact:
                yield artefact
            else:
                break

    def output(self, action: Node) -> Node:
        artefact_out = self.value(action, WF.output, any=False)
        assert artefact_out
        return artefact_out

    def sig_out(self, action: Node) -> list[Polytype]:
        return [self.type(self.output(action))]

    def sig_in(self, action: Node) -> list[Polytype]:
        return [self.type(artefact) for artefact in self.inputs(action)]

    def workflow_io(self, wf: Node) -> tuple[set[Node], set[Node]]:
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
            outputs.add(self.output(action))
        ginputs = inputs - outputs
        goutputs = outputs - inputs

        # assert len(goutputs) == 1, f"""There must be exactly 1 output, but 
        # {n3(wf)} has {len(goutputs)}."""
        assert set(self.objects(wf, WF.source)) == ginputs, """The sources of 
        the workflow don't match with the inputs"""

        return ginputs, goutputs

    @staticmethod
    def from_file(path: str | Path, format: str = "") -> ConcreteWorkflow:
        g = ConcreteWorkflow()
        g.parse(path, format=format or guess_format(str(path)))
        return g

    def extract_workflow_schema(self, wf: Node) -> Graph:
        """
        Extract a schematic workflow from a concrete one ("workflow instance").
        """

        g = GraphList()

        assert (wf, RDF.type, WF.Workflow) in self
        assert wf is not self.root

        # Concrete artefacts and actions to schematic ones
        schematic: dict[Node, BNode] = dict()

        g.add((wf, RDF.type, TOOLS.WorkflowSchema))

        # Figure out inputs/outputs to the workflow; add IDs where necessary
        sources, targets = self.workflow_io(wf)
        for i, artefact in enumerate(sources, start=1):
            a = schematic[artefact] = BNode(shorten(artefact))
            g.add((wf, TOOLS.input, a))
            g.add((a, TOOLS.id, Literal(i)))
        for artefact in targets:
            a = schematic[artefact] = BNode(shorten(artefact))
            g.add((wf, TOOLS.output, a))

        # Figure out intermediate actions
        for action in self.objects(wf, WF.edge):
            if action not in schematic:
                schematic[action] = BNode()
            for artefact in chain(self.inputs(action), [self.output(action)]):
                if artefact not in schematic:
                    schematic[artefact] = BNode(shorten(artefact))

            impl = self.implementation(action)
            g.add((wf, TOOLS.action, schematic[action]))
            g.add((schematic[action], TOOLS.apply, impl))
            for artefact in self.inputs(action):
                g.add((schematic[action], TOOLS.input, schematic[artefact]))
            g.add((schematic[action], TOOLS.output, 
                schematic[self.output(action)]))

        return g
