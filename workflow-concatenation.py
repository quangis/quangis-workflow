#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

import rdflib  # type: ignore
from rdflib import Graph
from rdflib.term import Node  # type: ignore
from glob import glob

from transformation_algebra.expr import Expr, Variable
from cct import cct

from typing import List, Tuple, Optional

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
GIS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
WF = rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")


def graph(*paths: str) -> rdflib.Graph:
    g = rdflib.Graph()
    for path in paths:
        g.parse(path, format=rdflib.util.guess_format(path))
    return g


class Workflow(object):

    tools = graph('workflows/ToolDescription_TransformationAlgebra.ttl')

    def __init__(self, source: Graph, root: Node):
        self.source: Graph = source
        self.root: Node = root

    def steps(self) -> List[Node]:
        "Get steps of the workflow."
        return list(self.source.objects(subject=self.root, predicate=WF.edge))

    def resource_expr(self, resource: Node) -> Tuple[Optional[Node], Expr]:
        "Get an algebra expression associated with a resource node."
        # May loop infinitely
        steps = list(self.source.subjects(predicate=WF.output, object=resource))
        if steps:
            # If there are any steps that produce the resource as output...
            step = steps[0]
            args = []
            for i in (WF.input1, WF.input2, WF.input3):

                input_resource = list(
                    self.source.objects(subject=step, predicate=i))

                if len(input_resource) > 0:
                    _, expr1 = self.resource_expr(input_resource[0])
                    args.append(expr1)

            tool = next(self.source.objects(subject=step,
                predicate=WF.applicationOf))

            expr_str = [str(expr)
                for expr in self.tools.objects(subject=tool,
                    predicate=TOOLS.algebraexpression)
            ][0]
            expr = cct.parse(expr_str)
            assert expr
            return tool, expr.supply(*args)
        else:
            # Else, it is not the output of a step, so just a variable for now
            return None, Variable()

    def output(self) -> List[Node]:
        "Find the output(s) of this workflow."
        result = []
        for step in self.steps():
            outputs = list(
                self.source.objects(subject=step, predicate=WF.output))
            if outputs:
                assert len(outputs) == 1
                if all([(None, i, outputs[0]) not in self.source
                        for i in (WF.input1, WF.input2, WF.input3)]):
                    result.append(outputs[0])
        return result

    def expr(self) -> Tuple[Optional[Node], Expr]:
        output_resource = self.output()[0]
        return self.resource_expr(output_resource)

    @staticmethod
    def workflows(graph: Graph) -> List[Workflow]:
        "Get workflows in an RDF graph."
        return [
            Workflow(graph, node)
            for node in graph.subjects(predicate=RDF.type, object=WF.Workflow)]


g = graph(
    "workflows/ToolDescription_TransformationAlgebra.ttl",
    *glob("workflows/**/*_cct.ttl"))

result = g.query(
    """
    SELECT ?wf WHERE {
        ?wf a wf:Workflow.
        ?wf wf:edge ?step.
        ?step wf:output ?output.
        ?output tools:applicationOf ?tool.
    }
    """, initNs={"wf": WF})

for row in result:
    print(row)

# for fn in glob("workflows/**/*_cct.ttl"):
#     print(fn)
#     for wf in Workflow.workflows(graph(fn)):
#         try:
#             wf.expr()
#         except Exception as e:
#             print(e)
