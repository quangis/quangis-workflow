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
from rdflib import Graph, URIRef
from rdflib.term import Node
from pathlib import Path
from typing import Iterator
from itertools import count

from cct import cct  # type: ignore
import transforge as tf
from quangis_workflows.namespace import n3, WF, RDF, CCD, CCT, TOOLS
from quangis_workflows.types import Polytype, Dimension

root_dir = Path(__file__).parent.parent
type_graph = Graph()
type_graph.parse(root_dir / "CoreConceptData.rdf", format="xml")

dimensions = [
    Dimension(root, type_graph)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]


class ToolRepository(Graph):
    """
    A tool repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs):
        super().__init__(*nargs, **kwargs)

    def collect(self, cwf: ConcreteWorkflow):
        for app, tool in cwf.subject_objects(WF.applicationOf):
            print(f"Handling {n3(tool)}.")
            print("Inputs:")
            print("; ".join(t.short() for t in cwf.inputs(app)))
            print("Outputs:")
            print("; ".join(t.short() for t in cwf.outputs(app)))
            print()


class ConcreteWorkflow(Graph):
    def __init__(self, root: URIRef, *nargs, **kwargs):
        self.root = root
        super().__init__(*nargs, **kwargs)

    def type(self, artefact: Node) -> Polytype:
        return Polytype.assemble(dimensions, self.objects(artefact, RDF.type))

    def term(self, action: Node) -> tf.Expr:
        expr_string = self.value(action, CCT.expression, any=False)
        return cct.parse(expr_string)

    def tool(self, action: Node) -> URIRef:
        tool = self.value(action, WF.applicationOf, any=False)
        assert isinstance(tool, URIRef)
        return tool

    def outputs(self, action: Node) -> Iterator[Polytype]:
        artefact = self.value(action, WF.output, any=False)
        assert artefact
        yield self.type(artefact)

    def inputs(self, action: Node) -> Iterator[Polytype]:
        for i in count(start=1):
            artefact = self.value(action, WF[f"input{i}"], any=False)
            if artefact:
                yield self.type(artefact)
            else:
                break

    @staticmethod
    def from_file(path: str | Path, root: URIRef) -> ConcreteWorkflow:
        g = ConcreteWorkflow(root)
        g.parse(path, format="turtle")
        return g


if __name__ == "__main__":
    cwf = ConcreteWorkflow.from_file(
        root_dir / "wffood.ttl", TOOLS.wfcrime_route)
    store = ToolStore()
    store.collect(cwf)
