"""
Workflow graph class that's easier to work with.
"""

from itertools import chain
from pathlib import Path
from rdflib import Graph  # type: ignore
from rdflib.namespace import RDF, RDFS  # type: ignore
from rdflib.term import Node, URIRef  # type: ignore

from config import tools_path, WF, TOOLS  # type: ignore

tools: Graph = Graph()
tools.parse(tools_path, format='ttl')


class Workflow(Graph):
    def __init__(self, path: Path):
        super().__init__()
        self.parse(path, format='ttl')

        self.path = path
        self.root = self.value(None, RDF.type, WF.Workflow, any=False)
        self.description = self.value(self.root, RDFS.comment)
        self.steps = set(self.objects(self.root, WF.edge))
        self.sources = set(self.objects(self.root, WF.source))

        # map output nodes to input nodes, tools and expressions
        self.output: Node
        self.outputs: set[Node] = set()
        self.inputs: dict[Node, list[Node]] = {}
        self.tools: dict[Node, URIRef] = {}
        self.expressions: dict[Node, str] = {}
        self.comment: dict[Node, str] = {}

        for step in self.steps:
            out = self.value(step, WF.output, any=False)
            self.outputs.add(out)

            self.tools[out] = tool = self.value(
                step, WF.applicationOf, any=False)
            assert tool, "workflow has an edge without a tool"

            self.expressions[out] = expr = tools.value(
                tool, TOOLS.algebraexpression, any=False)
            assert expr, f"{tool} has no algebra expression"

            if comment := self.value(step, RDFS.comment):
                self.comment[out] = comment

            self.inputs[out] = [node
                for pred in (WF.input1, WF.input2, WF.input3)
                if (node := self.value(step, pred))
            ]

        final_outputs = (self.outputs - set(chain.from_iterable(self.inputs.values())))
        assert len(final_outputs) == 1
        self.output, = final_outputs
