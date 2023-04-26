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
from rdflib import Graph
from rdflib.term import Node, BNode, URIRef, Literal
from rdflib.util import guess_format
from pathlib import Path
from itertools import count, chain
from collections import defaultdict
from typing import Iterator

from cct import cct  # type: ignore
from transforge.namespace import shorten
from quangis_workflows.namespace import (
    WF, RDF, CCD, CCT, CCT_, TOOLS, TOOL, DATA, OWL, SUPERTOOL, SIG, ARC, n3, 
    namespaces)
from quangis_workflows.types import Polytype, Dimension
from quangis_workflows.tool2url import tool2url

from transforge.list import GraphList

root_dir = Path(__file__).parent.parent
type_graph = Graph()
type_graph.parse(root_dir / "CoreConceptData.rdf", format="xml")

dimensions = [
    Dimension(root, type_graph)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]


def tool_to_url(node: Node, pattern=re.compile(r'(?<!^)(?=[A-Z])')) -> URIRef:
    name = shorten(node)
    return ARC[pattern.sub('-', name).lower() + ".htm"]


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

        self.input_keys: list[str] = sorted(inputs.keys())
        self.output_keys: list[str] = sorted(outputs.keys())
        self.transformation_p = cct.parse(transformation, defaults=True)

    def matches_purpose(self, candidate: Signature) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return self.transformation_p.match(candidate.transformation_p)

    def covers_datatype(self, candidate: Signature) -> bool:
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
        if not (self.input_keys == candidate.input_keys
                and self.output_keys == candidate.output_keys):
            return False

        return (
            all(candidate.inputs[k1].subtype(self.inputs[k2])
                for k1, k2 in zip(self.input_keys, self.input_keys))
            and all(self.outputs[k1].subtype(candidate.outputs[k2])
                for k1, k2 in zip(self.output_keys, self.output_keys))
        )

    def update(self, other: Signature) -> None:
        """Update this spec with information from another spec."""
        pass

    @staticmethod
    def propose(wf: ConcreteWorkflow, action: Node) -> Signature:
        """Create a new candidate signature from an action in a workflow."""
        tfm = wf.purpose(action)
        if not tfm:
            raise EmptyTransformationError(
                f"An action of {n3(wf.root)} that implements "
                f"{wf.implementation(action)[0]} has no transformation")
        sig = Signature(
            inputs={str(id): wf.type(artefact)
                for id, artefact in enumerate(wf.inputs(action), start=1)},
            outputs={str(id): wf.type(artefact)
                for id, artefact in enumerate(wf.outputs(action), start=1)},
            transformation=tfm
        )
        return sig


class ToolRepository(object):
    """
    A tool repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        super().__init__(*nargs, **kwargs)

        # Signatures (abstract tools)
        self.signatures: dict[URIRef, Signature] = dict()

        # Concrete tools
        self.tools: set[URIRef] = set()

        # Ensembles of concrete tools (workflow schemas)
        self.supertools: dict[URIRef, Graph] = dict()

    @staticmethod
    def from_file(self) -> ToolRepository:
        raise NotImplementedError

    def __contains__(self, sig: URIRef) -> bool:
        return sig in self.signatures

    def generate_name(self, base: str) -> URIRef:
        """
        Generate a name for an abstract tool based on an existing concrete 
        tool.
        """
        for i in chain("", count(start=1)):
            uri = SIG[f"{base}{i}"]
            if uri not in self:
                return uri
        raise RuntimeError("Unreachable")

    def signature(self, wf: ConcreteWorkflow, action: Node) -> URIRef:
        """Find out if any signature in this repository matches the action."""
        impl_name, impl = wf.implementation(action)
        proposal = Signature.propose(wf, action)
        for sig in self.signatures.values():
            if (impl in sig.implementations
                    and sig.covers_datatype(proposal)
                    and sig.matches_purpose(proposal)):
                return sig
        raise NoSignatureError(f"The repository contains no matching "
            f"signature for {n3(impl)}")

    def analyze_action(self, wf: ConcreteWorkflow,
            action: Node) -> URIRef | None:
        """
        Analyze a single action (application of a tool or workflow) and figure 
        out what spec it belongs to. As a side-effect, update the repository of 
        tool specifications if necessary.
        """
        impl_name, impl = wf.implementation(action)
        impl_orig = TOOLS[impl_name]

        if (action, CCT.expression, None) not in wf:
            # TODO don't require CCT expression?
            print(f"Skipping an application of {n3(impl)} because it "
                f"has no CCT expression.""")
            # return None

        # if not wf.basic(impl_orig):
        #     print(f"""Skipping an application of {n3(impl)} because it 
        #     contains subworkflows.""")
        #     return None

        # Is this implemented by ensemble of tools or a single concrete tool?
        if (impl_orig, RDF.type, WF.Workflow) in wf:
            if impl not in self.supertools:
                self.supertools[impl] = wf.extract_supertool(impl_orig, impl)
        else:
            self.tools.add(impl)

        try:
            candidate = Signature.propose(wf, action)
            candidate.implementations.add(impl)
        except EmptyTransformationError:
            print(f"""Skipping an application of {n3(impl)} because it has no 
            transformation expression.""")
            return None

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
            if not candidate.matches_purpose(sig):
                continue

            # Is the CCD type the same?
            if candidate.covers_datatype(sig):
                assert not supersig
                supersig = sig
            elif sig.covers_datatype(candidate):
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
            candidate.uri = self.generate_name(impl_name)
            self.signatures[candidate.uri] = candidate
            return candidate.uri

    def collect(self, wf: ConcreteWorkflow):
        for action, _ in wf.subject_objects(WF.applicationOf):
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
                if impl in self.supertools:
                    g.add((impl, TOOL.signature, sig.uri))

            inputs = []
            for i in sig.input_keys:
                artefact = BNode()
                for uri in sig.inputs[i].uris():
                    g.add((artefact, RDF.type, uri))
                inputs.append(artefact)
            g.add((sig.uri, TOOL.inputs, g.add_list(inputs)))

            outputs = []
            for i in sig.output_keys:
                artefact = BNode()
                for uri in sig.outputs[i].uris():
                    g.add((artefact, RDF.type, uri))
                outputs.append(artefact)
            g.add((sig.uri, TOOL.outputs, g.add_list(outputs)))

            g.add((sig.uri, CCT.expression, Literal(sig.transformation)))

        for tool, wf in self.supertools.items():
            g += wf

        return g


class ConcreteWorkflow(Graph):
    """
    Concrete workflow in old format.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self._root: Node | None = None
        super().__init__(*nargs, **kwargs)

    def type(self, artefact: Node) -> Polytype:
        return Polytype.assemble(dimensions, self.objects(artefact, RDF.type))

    def basic(self, impl: Node) -> bool:
        """Test if an implementation is basic, that is, it is either a concrete 
        tool or a workflow that does not have subworkflows."""

        if (impl, RDF.type, WF.Workflow) in self:
            return not any((subimpl, RDF.type, WF.Workflow) in self
                for action in self.objects(impl, WF.edge)
                for subimpl in self.objects(action, WF.applicationOf))
        else:
            return True

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

    def purpose(self, action: Node) -> str | None:
        a = self.value(action, CCT_.expression, any=False)
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

    def high_level_actions(self, wf: Node) -> Iterator[Node]:
        """Obtain the high-level actions of a workflow --- that is, actions 
        that are not also part of any subworkflow."""
        for action in self.objects(wf, WF.edge):
            if tuple(self.subjects(WF.edge, action)) == (wf,):
                yield action

    def abstraction(self, wf: Node, repo: ToolRepository, root: Node = None,
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
            inputs, outputs = self.workflow_io(wf)
            for predicate, artefacts in (
                    (WF.source, inputs), (WF.target, outputs)):
                for artefact in artefacts:
                    g.add((wf, predicate, artefact))

        for action in self.high_level_actions(wf):
            if self.basic(action):
                # assert (action, CCT.expression, None) in self
                sig = repo.signature(self, action)
                g.add((root, WF.edge, map[action]))
                g.add((map[action], WF.applicationOf, sig.uri))

                for i, artefact in enumerate(self.inputs(action), start=1):
                    g.add((map[action], WF[f"input{i}"], artefact))

                for pred, artefact in zip([WF.output], self.outputs(action)):
                    g.add((map[action], pred, artefact))

            else:
                assert not self.basic(action)
                subwf = self.value(wf, WF.applicationOf, any=False)
                self.convert_to_abstract(subwf, repo, root, (g, map))

        return g

    def extract_supertool(self, wf: Node, wf_schema: URIRef) -> Graph:
        """
        Extract a schematic workflow (in the TOOL namespace) from a concrete 
        one (a workflow instance in the WF namespace).
        """

        g = self.unfold(wf).schematic(wf_schema)

        # assert (wf, RDF.type, WF.Workflow) in self
        # assert wf is not self.root

        # def named_bnode(artefact: Node) -> BNode:
        #     return BNode(f"{shorten(wf)}_{shorten(artefact)}")

        # # Concrete artefacts and actions to schematic ones
        # map: dict[Node, Node] = defaultdict(BNode)
        # map[wf] = wf_schema

        # g.add((map[wf], RDF.type, TOOL.Supertool))

        # # Figure out inputs/outputs to the workflow
        # sources, targets = self.workflow_io(wf)
        # for artefact in chain(sources, targets):
        #     map[artefact] = named_bnode(artefact)

        # g.add((g.root, TOOL.inputs, g.add_list(
        #     [map[x] for x in self.inputs(action)])))
        # g.add((g.root, TOOL.outputs, g.add_list(
        #     [map[x] for x in self.outputs(action)])))

        # Figure out intermediate actions
        # for action in self.high_level_actions(wf):
        #     for artefact in chain(self.inputs(action), self.outputs(action)):
        #         if artefact not in map:
        #             map[artefact] = named_bnode(artefact)

        #     impl_name, impl = self.implementation(action)
        #     impl_orig = TOOLS[impl_name]
        #     assert impl_orig == self.value(action, WF.applicationOf, any=False)

        #     # if (impl_orig, RDF.type, WF.Workflow) not in self, \
        #     #     f"""actions of {n3(map[wf])} must apply only concrete tools, 
        #     #     but {n3(impl)} is a supertool"""

        #     g.add((map[wf], TOOL.action, map[action]))
        #     g.add((map[action], TOOL.apply, impl))
        #     g.add((map[action], TOOL.inputs, g.add_list(
        #         [map[artefact] for artefact in self.inputs(action)])))
        #     g.add((map[action], TOOL.outputs, g.add_list(
        #         [map[artefact] for artefact in self.outputs(action)])))

        return g

    def schematic(self, uri: Node) -> GraphList:
        """Turn a concrete workflow into a schematic workflow by turning all 
        the data nodes into blank nodes."""
        g = GraphList()
        map: dict[Node, Node] = defaultdict(BNode)
        map[self.root] = uri
        for a in self.high_level_actions(self.root):
            impl = self.value(a, WF.applicationOf, any=False)
            g.add((uri, TOOL.action, map[a]))
            g.add((map[a], TOOL.apply, impl))
            g.add((map[a], TOOL.inputs,
                g.add_list(map[x] for x in self.inputs(a))))
            g.add((map[a], TOOL.outputs,
                g.add_list(map[x] for x in self.outputs(a))))
        return g

    def unfold(self, root: Node | None = None,
            g: Graph | None = None) -> ConcreteWorkflow:
        """Extract lowest-level workflow into the given graph."""
        root = root or self.root

        if not g:
            g = ConcreteWorkflow()
            g.add((g, RDF.type, WF.Workflow))

        for a in self.high_level_actions(root):
            impl = self.value(a, WF.applicationOf, any=False)
            if (impl, RDF.type, WF.Workflow) in self:
                self.unfold(root=impl, g=g)
            else:
                g.add((g.root, WF.edge, a))
                g.add((a, WF.applicationOf, impl))

                for i, artefact in enumerate(self.inputs(a), start=1):
                    pred = TOOL[f"input{i}"]
                    g.add((a, pred, artefact))

                for pred, artefact in zip([TOOL.output], self.outputs(a)):
                    g.add((a, pred, artefact))
        return g
