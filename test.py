#!/usr/bin/env python3
from __future__ import annotations
import unittest
from rdflib import Graph, RDF, RDFS, Namespace
from rdflib.term import Node
from pathlib import Path
from typing import Iterable

WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
root_path = Path(__file__).parent


def parameterized(params: Iterable):
    "Turn a test case into a suite of parameterized test cases."
    testloader = unittest.TestLoader()

    def decorator(cls: type) -> unittest.TestSuite:
        suite = unittest.TestSuite()
        for testname in testloader.getTestCaseNames(cls):
            for param in params:
                suite.addTest(cls(testname, param))
        return suite

    return decorator


    # for param in params:
    #     wf = path.stem
    #     graph = Graph()
    #     graph.parse(path)
    #     root = graph.value(None, RDF.type, WF.Workflow, any=False)
    #     assert root

    #     class TestWorkflow1(cls):
    #         def setUp(self):
    #             self.wf = wf
    #             self.graph = graph
    #             self.root = root

    #     testnames = testloader.getTestCaseNames(cls)
    #     for name in testnames:
    #         suite.addTest(TestWorkflow1(name))
    # return suite


@parameterized(root_path.glob("workflows/*.ttl"))
class TestWorkflow(unittest.TestCase):
    def __init__(self, runMethod: str, path: Path):
        super().__init__(runMethod)
        self.wf = path.stem
        self.graph = Graph()
        self.graph.parse(path)
        self.root = self.graph.value(None, RDF.type, WF.Workflow, any=False)

    def test_every_node_has_an_existing_tool(self):
        # Every node (indicated by wf:edge) in a workflow should have a tool
        # (indicated by wf:applicationOf). Each of those tools must exist in
        # the tool ontology.
        for step in self.graph.objects(self.root, WF.edge):
            label = str(self.graph.value(step, RDFS.comment, any=False))
            with self.subTest(step_label=label):
                self.assertIsNone(self.graph.value(step,
                    WF.applicationOf, any=False))
                # TODO must exist


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
    # unittest.main()
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(TestWorkflow)
