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
from typing import Iterator

from cct import cct  # type: ignore
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


class EmptyTransformationError(Exception):
    pass


class Action(object):
    pass


class Signature(object):
    """A tool signature is an abstract specification of a tool. It may 
    correspond to one or more concrete tools, or even ensembles of tools. It 
    must describe the format of its input and output (ie the core concept 
    datatypes) and it must describe its purpose (in terms of a core concept 
    transformation expression).

    A signature may be implemented by multiple (workflows of) concrete tools, 
    because, for example, a tool could be implemented in both QGIS and ArcGIS. 
    Conversely, multiple specifications may be implemented by the same concrete 
    tool/workflow, if it can be used in multiple contexts --- in the same way 
    that a hammer can be used both to drive a nail into a plank of wood or to 
    break a piggy bank."""

    def __init__(self,
            inputs: dict[str, Polytype],
            outputs: dict[str, Polytype],
            transformation: str) -> None:
        self.inputs: dict[str, Polytype] = inputs
        self.outputs: dict[str, Polytype] = outputs
        self.transformation: str = transformation

        self.uri: URIRef | None = None
        self.description: str | None = None
        self.implementations: set[URIRef] = set()

        self.inputs_keys = set(inputs.keys())
        self.outputs_keys = set(outputs.keys())
        self.transformation_p = cct.parse(transformation, defaults=True)

    def match_implementation(self, candidate: Signature) -> bool:
        """Check that the implementations (tools or workflows) in the candidate 
        signature are also in the current one."""
        raise NotImplementedError

    def match_purpose(self, candidate: Signature) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return self.transformation_p.match(candidate.transformation_p)

    def match_datatype(self, candidate: Signature) -> bool:
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
        if not (self.inputs_keys == candidate.inputs_keys
                and self.outputs_keys == candidate.outputs_keys):
            return False

        return (
            all(candidate.inputs[k1].subtype(self.inputs[k2])
                for k1, k2 in zip(self.inputs_keys, self.inputs_keys))
            and all(self.outputs[k1].subtype(candidate.outputs[k2])
                for k1, k2 in zip(self.inputs_keys, self.inputs_keys))
        )

    def update(self, other: Signature) -> None:
        """Update this spec with information from another spec."""
        pass

    @staticmethod
    def propose(wf: ConcreteWorkflow, action: Node) -> Signature:
        """Create a new candidate signature from an action in a workflow."""
        tfm = wf.transformation(action)
        if not tfm:
            raise EmptyTransformationError
        sig = Signature(
            inputs={str(i): wf.type(artefact)
                for i, artefact in enumerate(wf.inputs(action))},
            outputs={str(i): wf.type(artefact)
                for i, artefact in enumerate(wf.outputs(action))},
            transformation=tfm
        )
        sig.implementations.add(wf.implementation(action))
        return sig


class ToolRepository(object):
    """
    A tool repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        # Signatures (abstract tools)
        # self.sigs: dict[URIRef, Signature] = dict()
        # self.signatures: set[Signature] = set()
        self.signatures: dict[URIRef, Signature] = dict()

        # Concrete tools
        self.tools: set[URIRef] = set()

        # Ensembles of concrete tools (workflow schemas)
        self.workflows: dict[URIRef, Graph] = dict()

    def __contains__(self, sig: URIRef) -> bool:
        return sig in self.signatures

    def generate_name(self, base: URIRef) -> URIRef:
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
            action: Node) -> URIRef | None:
        """
        Analyze a single action (application of a tool or workflow) and figure 
        out what spec it belongs to. As a side-effect, update the repository of 
        tool specifications if necessary.
        """
        impl = wf.implementation(action)

        try:
            candidate = Signature.propose(wf, action)
        except EmptyTransformationError:
            return None

        # Is this implemented by ensemble of tools or a single concrete tool?
        if (impl, RDF.type, WF.Workflow) in wf:
            if impl not in self.workflows:
                subwf = wf.extract_workflow_schema(impl)
                self.workflows[impl] = subwf
        else:
            self.tools.add(impl)

        # Find out how other signatures relate to the candidate sig
        supersig: Signature | None = None
        subsigs: list[Signature] = []
        for uri, sig in self.signatures.items():
            # Is the URI the same?
            if impl not in sig.implementations:
                continue

            # Is the CCT expression the same?
            if not candidate.match_purpose(sig):
                continue

            # Is the CCD type the same?
            if candidate.match_datatype(sig):
                assert not supersig
                supersig = sig
            elif sig.match_datatype(candidate):
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
            candidate.uri = self.generate_name(impl)
            self.signatures[candidate.uri] = candidate
            return candidate.uri

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


class ToolRepositoryGraph(Graph):

    def __init__(self, repo: ToolRepository) -> None:
        super().__init__()

        self.bind("", TOOLS)
        self.bind("ccd", CCD)
        self.bind("cct", CCT)
        self.bind("data", DATA)

        for sig in repo.signatures.values():
            assert isinstance(sig.uri, URIRef)
            for impl in sig.implementations:
                self.add((sig.uri, TOOLS.implementedBy, impl))

            for i, t in sig.inputs.items():
                a = self.add_artefact(t)
                self.add((sig.uri, TOOLS.input, a))
                self.add((a, TOOLS.id, Literal(i)))

            for i, t in sig.outputs.items():
                a = self.add_artefact(t)
                self.add((sig.uri, TOOLS.output, a))
                self.add((a, TOOLS.id, Literal(i)))

            self.add((sig.uri, CCT.expression, Literal(sig.transformation)))

        for tool in repo.tools:
            self.add((tool, RDF.type, TOOLS.Tool))

        for tool, wf in repo.workflows.items():
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

    def transformation(self, action: Node) -> str | None:
        return self.value(action, CCT.expression, any=False)

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

    def outputs(self, action: Node) -> Iterator[Node]:
        artefact_out = self.value(action, WF.output, any=False)
        assert artefact_out
        yield artefact_out

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
            outputs.update(self.outputs(action))
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
        Extract a schematic workflow (in the TOOLS namespace) from a concrete 
        one (a workflow instance in the WF namespace).
        """

        g = Graph()

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
            for artefact in chain(self.inputs(action), self.outputs(action)):
                if artefact not in schematic:
                    schematic[artefact] = BNode(shorten(artefact))

            impl = self.implementation(action)
            g.add((wf, TOOLS.action, schematic[action]))
            g.add((schematic[action], TOOLS.apply, impl))
            for artefact in self.inputs(action):
                g.add((schematic[action], TOOLS.input, schematic[artefact]))
            for artefact in self.outputs(action):
                g.add((schematic[action], TOOLS.output, schematic[artefact]))

        return g
