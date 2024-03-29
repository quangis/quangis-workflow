"""A concrete workflow is a graph that consists solely of actions 
(*applications* of tool implementations), along with CCT-terms that express 
their functionality, plus artefacts (their concrete inputs and outputs), along 
with CCD annotations.

Additionally, in the case that a single tool cannot be expressed meaningfully 
with a CCT-term, the graph may include ad-hoc "supertool" applications, which 
point to an *ensemble* of tool applications that can be given a term 
collectively."""

from __future__ import annotations

from rdflib import Graph
from rdflib.term import Node, URIRef, Literal, BNode
from rdflib.util import guess_format
from pathlib import Path
from itertools import count
from typing import Iterator

from transforge.namespace import shorten
from quangis.namespace import (
    WF, RDF, RDFS, CCT, CCT_, n3)
from quangis.polytype import Polytype
from quangis.ccd import ccd

root_dir = Path(__file__).parent.parent

class Workflow(Graph):
    """
    Concrete workflow in old format.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self._root: Node | None = None
        super().__init__(*nargs, **kwargs)

    @staticmethod
    def from_file(path: str | Path, format: str = "") -> Workflow:
        g = Workflow()
        g.parse(path, format=format or guess_format(str(path)))
        return g

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
        return Polytype(ccd.dimensions, self.objects(artefact, RDF.type))

    def cct_expr(self, action: Node) -> str | None:
        a = (self.value(action, CCT_.expression, any=False) or
            self.value(action, CCT.expression, any=False))
        if isinstance(a, Literal):
            return str(a)
        elif not a:
            return None
        raise RuntimeError("Core concept transformation must be literal")

    def inputs(self, action: Node, labelled: bool = False) -> Iterator[Node]:
        for i in count(start=1):
            artefact = self.value(action, WF[f"input{i}"], any=False)
            if artefact:
                yield artefact
            else:
                break

        unlabelled_inputs = list(self.objects(action, WF.inputx))
        if labelled and len(unlabelled_inputs) > 1:
            subwf = self.value(None, WF.edge, action)
            impl = self.value(action, WF.applicationOf)
            assert subwf and impl
            subwf_label = self.label(subwf)
            impl_label = self.label(impl)
            raise RuntimeError(
                f"Expected labelled inputs of an action that applies "
                f"'{impl_label}' in workflow '{subwf_label}'")
        else:
            yield from unlabelled_inputs

    def inputs_labelled(self, action: Node) -> dict[str, Node]:
        result = dict()
        for i in count(start=1):
            artefact = self.value(action, WF[f"input{i}"], any=False)
            if artefact:
                result[str(i)] = artefact
            else:
                break

        # A single `inputx` is (temporarily?) interpreted as `input1`
        inputx = self.value(action, WF.inputx, any=False)
        if result:
            if inputx:
                raise RuntimeError(
                    f"An action contains both {n3(WF.input1)} and "
                    f"{n3(WF.inputx)} predicates.")
        elif inputx:
            result["1"] = inputx

        return result

    def output(self, action: Node) -> Node:
        artefact_out = self.value(action, WF.output, any=False)
        if artefact_out:
            return artefact_out
        else:
            raise RuntimeError("no output artefact")

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

    def high_level_actions(self, root: Node) -> set[Node]:
        """Actions that are part of the root workflow, but not also part of any 
        of its subworkflows."""
        assert (root, RDF.type, WF.Workflow) in self
        actions = set(self.objects(root, WF.edge))
        subactions = set(subaction
            for action in actions
            for subwf in self.objects(action, WF.applicationOf)
            for subaction in self.objects(subwf, WF.edge)
        )
        return actions - subactions

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

    def label(self, node: Node) -> str:
        label = self.value(node, RDFS.label, any=False)
        if label:
            return str(label)
        elif isinstance(node, URIRef):
            return shorten(node)
        else:
            raise RuntimeError("Cannot determine label of a blank node")

    def subworkflow(self, action: Node) -> BNode:
        subwf = self.impl(action)
        assert (subwf, RDF.type, WF.Workflow) in self
        assert isinstance(subwf, BNode)
        return subwf

    def tool(self, action: Node) -> URIRef:
        tool = self.impl(action)
        assert not (tool, RDF.type, WF.Workflow) in self
        assert isinstance(tool, URIRef)
        return tool

    def impl(self, action: Node) -> Node:
        impl = self.value(action, WF.applicationOf, any=False)
        assert impl
        return impl
