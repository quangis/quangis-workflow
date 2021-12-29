"""
Workflow graph class that's easier to work with.
"""

from rdflib import Graph
from rdflib.namespace import RDF, RDFS
from rdflib.term import Node, URIRef
import rdflib.util

from cct import cct
from config import root_path, WF, TOOLS

tools: Graph = Graph()
tools.parse(root_path / 'rdf' / 'tools.ttl', format='ttl')


class Workflow(Graph):
    def __init__(self, fn: str):
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
            assert tool, "workflow has an edge without a tool"

            self.expressions[out] = expr = tools.value(
                tool, TOOLS.algebraexpression, any=False)
            assert expr, f"{tool} has no algebra expression"

            self.inputs[out] = list(filter(bool, (
                self.value(step, p) for p in (WF.input1, WF.input2, WF.input3)
            )))
