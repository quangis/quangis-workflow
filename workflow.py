"""
Workflow graph class that's easier to work with.
"""

from rdflib import Graph
from rdflib.namespace import RDF, RDFS
from rdflib.term import Node, URIRef
import rdflib.util
from typing import Union

from transformation_algebra import Expr

from cct import cct
from util import WF, TOOLS


class Workflow(Graph):
    def __init__(self, fn: str, tools: Graph):
        super().__init__()
        self.parse(fn, format=rdflib.util.guess_format(fn))

        self.file = fn
        self.root = self.value(None, RDF.type, WF.Workflow, any=False)
        self.description = self.value(self.root, RDFS.comment)
        self.steps = set(self.objects(self.root, WF.edge))
        self.sources = set(self.objects(self.root, WF.source))

        # map output nodes to input nodes, tools and expressions
        self.outputs: set[Node] = set()
        self.inputs: dict[Node, list[Node]] = {}
        self.tools: dict[Node, URIRef] = {}
        self.expressions: dict[Node, str] = {}
        for step in self.steps:
            out = self.value(step, WF.output, any=False)
            self.outputs.add(out)
            self.tools[out] = tool = self.value(
                step, WF.applicationOf, any=False)
            self.expressions[out] = expr = tools.value(
                tool, TOOLS.algebraexpression, any=False)
            self.inputs[out] = list(filter(bool, (
                self.value(step, p) for p in (WF.input1, WF.input2, WF.input3)
            )))

            assert tool, "workflow has an edge without a tool"
            assert expr, f"{tool} has no algebra expression"

    def format(self) -> dict[Node, tuple[Expr, list[Node]]]:
        return {
            output: (cct.parse(self.expressions[output]).primitive(), inputs)
            for output, inputs in self.inputs.items()
        }

    def format2(self) -> dict[Expr, list[Union[Node, Expr]]]:
        """
        Map expressions to their inputs.
        """
        expressions: dict[Node, Expr] = {
            node: cct.parse(expr).primitive()
            for node, expr in self.expressions.items()
        }

        return {
            expressions[output]: list(expressions.get(i, i) for i in inputs)
            for output, inputs in self.inputs.items()
        }
