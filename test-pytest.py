#!/usr/bin/env python3
from __future__ import annotations
import pytest
from rdflib import Graph, RDF, RDFS, Namespace
from rdflib.term import Node
from pathlib import Path
from typing import Iterator

WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
root_path = Path(__file__).parent

# Check whether the files are consistent with the workflow schema. Every tool
# must have a corresponding description. Every tool in a scenario workflow must
# exist in the tools ontology. Check whether blank nodes are never used in
# multiple tools. All blank nodes should only ever be reused in the same
# supertool workflow. Every signature should have at least one input and one
# output. Every abstract tool should either be implemented by a concrete tool,
# or it should be a supertool, or it should be implemented by a supertool. An
# abstract tool is a tool that has a semantics in terms of a CCD signature; a
# supertool might not have a CCD signature, in which case it must implement an
# abstract tool.


@pytest.fixture(scope="module")
def tools() -> Graph:
    graph = Graph()
    graph.parse(root_path / "tools" / "tools.ttl")
    return graph


@pytest.fixture(scope="module")
def workflows() -> Graph:
    graph = Graph()
    for path in root_path.glob("workflows/*.ttl"):
        graph.parse(path)
    return graph


def test_every_node_has_an_existing_tool(subtests, tools: Graph, workflows: Graph):
    # Every node (indicated by wf:edge) in a workflow should have a tool
    # (indicated by wf:applicationOf). Each of those tools must exist in
    # the tool ontology.
    for wf in workflows.subjects(RDF.type, WF.Workflow):
        for step in workflows.objects(wf, WF.edge):
            label = str(workflows.value(step, RDFS.comment, any=False))
            with subtests.test(wf=wf, label=label):
                assert workflows.value(step, WF.applicationOf, any=False) is None
                # TODO must exist
