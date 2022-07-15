#!/usr/bin/env python3
from __future__ import annotations
import unittest
from rdflib import Graph, RDF, Namespace
from rdflib.term import Node
from pathlib import Path

WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
root_path = Path(__file__).parent


def testWorkflows(path: Path) -> unittest.TestSuite:
    wf = path.stem
    graph = Graph()
    graph.parse(path)
    root = graph.value(None, RDF.type, WF.Workflow, any=False)
    assert root

    class TestWorkflow1(unittest.TestCase):
        def setUp(self):
            self.wf = wf
            self.graph = graph
            self.root = root

        def test_every_node_has_a_tool(self):
            """
            Every node (indicated by wf:edge) in a workflow should have a
            tool (indicated by wf:applicationOf).
            """
            with self.subTest(name=self.wf):
                for step in self.graph.objects(self.root, WF.edge):
                    self.assertIsNone(self.graph.value(step,
                        WF.applicationOf, any=False))

    testloader = unittest.TestLoader()
    testnames = testloader.getTestCaseNames(TestWorkflow1)
    suite = unittest.TestSuite()
    for name in testnames:
        suite.addTest(TestWorkflow1(name))
    return suite


class TestTools(unittest.TestCase):
    # Check whether the files are consistent with the workflow schema. Every
    # tool must have a corresponding description. Every tool in a scenario
    # workflow must exist in the tools ontology. Check whether blank nodes are
    # never used in multiple tools. All blank nodes should only ever be reused
    # in the same supertool workflow. Every signature should have at least one
    # input and one output. Every abstract tool should either be implemented by
    # a concrete tool, or it should be a supertool, or it should be implemented
    # by a supertool. An abstract tool is a tool that has a semantics in terms
    # of a CCD signature; a supertool might not have a CCD signature, in which
    # case it must implement an abstract tool.
    def setUp(self):
        self.tools = Graph()
        self.tools.parse(root_path / "tools" / "tools.ttl")

    @unittest.expectedFailure
    def hello(self):
        pass


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestSuite()
    for path in root_path.glob("workflows/*.ttl"):
        suite.addTest(testWorkflows(path))
    result = runner.run(suite)
