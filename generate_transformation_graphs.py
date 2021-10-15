#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

import os.path
from rdflib import Graph  # type: ignore
from rdflib.namespace import RDF  # type: ignore
from rdflib.term import Node  # type: ignore
from glob import glob
from sys import stderr

from transformation_algebra.expr import Expr
from transformation_algebra.rdf import TransformationGraph

from cct import CCT, cct  # type: ignore
from util import write_graph, graph, WF, TOOLS  # type: ignore


def get_steps(workflows: Graph, tools: Graph, wf: Node
        ) -> dict[Node, tuple[Expr, list[Node]]]:
    """
    Map the output node of each step to an expression and its input nodes.
    """
    steps = {}
    for step in workflows.objects(wf, WF.edge):
        tool = workflows.value(step, WF.applicationOf, any=False)
        assert tool, "workflow has an edge without a tool"
        expr = tools.value(tool, TOOLS.algebraexpression, any=False)
        assert expr, f"{tool} has no algebra expression"
        output = workflows.value(step, WF.output, any=False)
        steps[output] = cct.parse(expr).primitive(), list(filter(bool, (
            workflows.value(step, p) for p in (WF.input1, WF.input2, WF.input3)
        )))
    return steps


def workflow_expr(workflows: Graph, tools: Graph, workflow: Node) -> Graph:
    """
    Concatenate workflow expressions and add them to a graph.
    """

    # Find expressions for each step by mapping the output node of each to the
    # algebra expression associated with the tool, and the input nodes
    steps = get_steps(workflows, tools, workflow)
    sources = set(workflows.objects(subject=workflow, predicate=WF.source))

    output = TransformationGraph(cct, CCT)
    output.add_workflow(workflow, sources, steps)
    return output


cct_graph = TransformationGraph.vocabulary(cct, CCT)
cct_graph.bind("cct", CCT)
write_graph(cct_graph, "cct_vocabulary")

tool_graph = graph(
    "TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl"
)

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):

    print(f"\nWorkflow {workflow_file}", file=stderr)

    workflow_graph = graph(workflow_file)
    workflow = workflow_graph.value(None, RDF.type, WF.Workflow, any=False)

    try:
        g = workflow_expr(workflow_graph, tool_graph, workflow)
    except Exception as e:
        print("Failure: ", e, file=stderr)
    else:
        print("Success!", file=stderr)
        write_graph(g, os.path.splitext(os.path.basename(workflow_file))[0])
