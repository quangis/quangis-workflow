#!/usr/bin/env python3
# This file contains sanity checks on our tool ontology and workflow
# repositories. Perhaps some of these sanity checks are better done by
# validating against a schema; cf. https://www.w3.org/2012/12/rdf-val/SOTA;
# http://book.validatingrdf.com/; https://shex.io/shex-primer/;
# https://www.w3.org/TR/shacl/.

# An abstract tool is a tool that has a semantics in terms of a CCD signature;
# a supertool might not have a CCD signature, in which case it must implement
# an abstract tool.

from __future__ import annotations
import unittest
from rdflib import Graph, RDF, RDFS, Namespace, URIRef, Literal
from rdflib.graph import Seq
from rdflib.collection import Collection
from rdflib.term import Node
from pathlib import Path
from inspect import signature

TOOLS = Namespace('https://github.com/quangis/cct/blob/master/tools/tools.ttl#')
WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
CCT = Namespace('https://github.com/quangis/cct#')

root_path = Path(__file__).parent
graph = Graph()
graph.parse(root_path / "tools" / "tools.ttl")
for path in root_path.glob("workflows/*.ttl"):
    graph.parse(path)

workflows = set(graph.subjects(RDF.type, WF.Workflow))
tools = set(graph.subjects(RDF.type / (RDFS.subClassOf * '+'), TOOLS.Tool))


def params(nodes):
    def decorator(f):
        def wrapper(self):
            for node in nodes:
                yield lambda n3, n: f(self, n), (
                    node.n3(namespace_manager=graph.namespace_manager), node)
        return wrapper
    return decorator


class NodeTester(type):

    def __new__(cls, name, bases, attrs):
        methods = {name: f
            for name, f in attrs.items() if name.startswith('test_')}

        for testname, f in methods.items():
            parameters = signature(f).parameters

            if "wf" in parameters:
                nodes = workflows
            elif "tool" in parameters:
                nodes = tools
            else:
                nodes = ()

            for node in nodes:
                nodename = node.n3(namespace_manager=graph.namespace_manager)
                name = f'{testname} for {nodename}'
                g = lambda self, node=node: f(self, tool=node)
                g.__name__ = name
                attrs[name] = g
            del attrs[testname]
        return type.__new__(cls, name, bases, attrs)


class Tests(unittest.TestCase, metaclass=NodeTester):

    # @params(workflows)
    def test_every_step_in_a_workflow_applies_an_existing_tool(self, wf: Node):
        # Every node (indicated by wf:edge) in a workflow should have a tool
        # (indicated by wf:applicationOf). Every tool in a scenario workflow
        # must exist in the tools ontology.
        for step in graph.objects(wf, WF.edge):
            label = graph.value(step, RDFS.comment)
            with self.subTest(step=str(label)):
                tool = graph.value(step, WF.applicationOf, any=False)
                self.assertIsNotNone(tool)
                self.assertIn(tool, tools)
        assert False

    # def test_every_tool_has_a_type(self, tool: Node):
    #     # Every tool is either an implementation, a specification or a
    #     # supertool; and it cannot be any multiple of these
    #     types = list(graph.objects(tool, RDF.type))
    #     self.assertEqual(len(types), 1)
    #     for type in types:
    #         self.assertIn(type, [TOOLS.ToolImplementation,
    #             TOOLS.ToolCombination,
    #             TOOLS.PartialToolSpecification,
    #             TOOLS.CompleteToolSpecification])

# # @unittest.expectedFailure
# @params(*tools)
# def test_every_tool_has_a_description(self, tool: Node):
#     # Every tool must have a corresponding description.
#     with self.subTest(tool=str(tool)):
#         expr = toolRDF.value(tool, RDFS.comment, any=False)
#         self.assertIsInstance(expr, Literal)

# # @unittest.skip("later")
# # @params(*tools)
# # def test_blank_nodes_are_never_reused_in_other_tools(self, tool: Node):
# #     # Check whether blank nodes are never used as input or output of
# #     # multiple tools.
# #     pass

# # def test_blank_nodes_are_never_reused_in_other_workflows(self):
# #     pass

# # @params(*tools)
# # def test_each_tool_should_have_some_input_and_output(self, tool: Node):
# #     pass

# # def test_implementations(self):
# #     # Every abstract tool should either be implemented by a concrete tool,
# #     # or it should be a supertool, or it should be implemented by a
# #     # supertool.
# #     pass


if __name__ == '__main__':
    import nose2  # type: ignore
    nose2.main()
