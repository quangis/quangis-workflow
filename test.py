#!/usr/bin/env python3
# This file contains sanity checks on our tool ontology and workflow
# repositories. Perhaps some of these sanity checks are better done by
# validating against a schema; cf. https://www.w3.org/2012/12/rdf-val/SOTA;
# http://book.validatingrdf.com/; https://shex.io/shex-primer/;
# https://www.w3.org/TR/shacl/.

from __future__ import annotations
import unittest
from rdflib import Graph, RDF, RDFS, Namespace, Literal
from rdflib.term import Node
from pathlib import Path
from itertools import chain
from typing import Iterable
from cct import cct
from transformation_algebra import Source

TOOLS = Namespace('https://github.com/quangis/cct/blob/master/tools/tools.ttl#')
WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
CCT = Namespace('https://github.com/quangis/cct#')

root_path = Path(__file__).parent
graph = Graph()
graph.parse(root_path / "tools" / "tools.ttl")
for path in root_path.glob("workflows/*.ttl"):
    graph.parse(path)


def io(node: Node) -> tuple[list[Node], Node]:
    """
    Obtain the set of inputs of a node. This should be done differently later,
    since having input{i}s instead of a rdf:Seq isn't the right way anyway.
    """
    inputs = []
    for i in range(1, 4):
        input = graph.value(node, WF[f"input{i}"], any=False)
        if input is None:
            for j in range(i, 4):
                assert graph.value(node, WF[f"input{j}"]) is None
        else:
            inputs.append(input)
    return inputs, graph.value(node, WF.output, any=False)


def nodes(*nodes: Iterable[Node]):
    """
    A decorator on test methods that generates a separate test method for each
    node in each iterable of nodes.
    """
    def decorator(f):
        def wrapper(self):
            for node in sorted(set(chain(*nodes))):
                yield lambda n3, n: f(self, n), (
                    node.n3(namespace_manager=graph.namespace_manager), node)
        return wrapper
    return decorator


class Tests(unittest.TestCase):

    @nodes(graph.subjects(RDF.type, WF.Workflow))
    def test_step_in_a_workflow_applies_an_existing_tool(self, wf: Node):
        # Every node (indicated by wf:edge) in a workflow should have a tool
        # (indicated by wf:applicationOf). Every tool in a scenario workflow
        # must exist in the tools ontology.
        for step in graph.objects(wf, WF.edge):
            label = graph.value(step, RDFS.comment)
            with self.subTest(step=str(label)):
                tool = graph.value(step, WF.applicationOf, any=False)
                self.assertIsNotNone(tool)
                self.assertIn(
                    (tool, RDF.type / (RDFS.subClassOf * '+'), TOOLS.Tool),
                    graph)

    @nodes(graph.subjects(RDF.type / (RDFS.subClassOf * '+'), TOOLS.Tool))
    def test_tool_has_a_unique_class(self, tool: Node):
        # Every tool is either an implementation, a specification or a
        # supertool; and it cannot be any multiple of these
        types = list(graph.objects(tool, RDF.type))
        self.assertEqual(len(types), 1)
        for type in types:
            self.assertIn(type, [TOOLS.ToolImplementation,
                TOOLS.ToolCombination,
                TOOLS.PartialToolSpecification,
                TOOLS.CompleteToolSpecification])

    @nodes(graph.subjects(RDF.type / RDFS.subClassOf, TOOLS.ToolSpecification))
    def test_abstract_tool_has_a_description(self, tool: Node):
        # Every tool specification must have a corresponding description.
        expr = graph.value(tool, RDFS.comment, any=False)
        self.assertIsInstance(expr, Literal)

    @nodes(graph.subjects(RDF.type, TOOLS.ToolImplementation))
    def test_concrete_tool_implement_some_abstract_tool(self, tool: Node):
        specs = list(graph.objects(tool, TOOLS.implements))
        self.assertGreaterEqual(len(specs), 1)
        for spec in specs:
            type = graph.value(spec, RDF.type, any=False)
            self.assertIn(type, [TOOLS.CompleteToolSpecification,
                TOOLS.PartialToolSpecification])

    @nodes(graph.subjects(RDF.type, TOOLS.ToolCombination))
    def test_supertool_implements_some_abstract_tool(self, tool: Node):
        specs = list(graph.objects(tool, TOOLS.implements))
        self.assertGreaterEqual(len(specs), 1)
        for spec in specs:
            type = graph.value(spec, RDF.type, any=False)
            self.assertEqual(type, TOOLS.CompleteToolSpecification)

    @nodes(
        graph.subjects(RDF.type / RDFS.subClassOf, TOOLS.ToolSpecification),
        graph.subjects(RDF.type / RDFS.subClassOf, TOOLS.ToolCombination)
    )
    def test_abstract_tool_should_have_input_and_output(self, tool: Node):
        inputs, output = io(tool)
        self.assertNotEqual(inputs, [])
        self.assertNotEqual(output, None)

    @nodes(graph.subjects(RDF.type, TOOLS.ToolCombination))
    def test_supertool_blank_nodes_never_reused(self, tool: Node):
        for step in graph.objects(tool, WF.edge):
            tool1 = graph.value(None, WF.edge, step, any=False)
            self.assertEqual(tool, tool1)

    @nodes(graph.subjects(RDF.type / RDFS.subClassOf, TOOLS.ToolSpecification))
    def test_input_and_outputs_are_never_reused(self, tool: Node):
        inputs, output = io(tool)
        for node in inputs + [output]:
            tool1 = graph.value(None, WF.edge, node, any=False)
            self.assertEqual(tool, tool1)

    @nodes(graph.subjects(RDF.type, TOOLS.ToolCombination))
    def test_tool_declares_all_inputs_and_output(self, tool: Node):
        steps = set(graph.objects(tool, WF.edge))
        sources = set(graph.objects(tool, WF.source))
        declared = set.union(steps, sources)
        for step in steps:
            inputs, output = io(step)
            for input in inputs:
                self.assertIn(input, declared)
            self.assertIn(output, steps)

    @nodes(graph.subjects(RDF.type, TOOLS.CompleteToolSpecification))
    def test_every_complete_spec_has_a_valid_cct_expression(self, tool: Node):
        expr = graph.value(tool, CCT.expression, any=False)
        self.assertIsNotNone(expr)
        self.assertIsInstance(expr, Literal)
        inputs, outputs = io(tool)
        cct.parse(str(expr), *(Source() for node in inputs))


if __name__ == '__main__':
    import nose2  # type: ignore
    nose2.main()
