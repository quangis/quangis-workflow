#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

from rdflib import Graph  # type: ignore
from rdflib.namespace import RDF  # type: ignore
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from glob import glob
from sys import stderr
from os.path import basename

from transformation_algebra.expr import Expr
from transformation_algebra.rdf import TransformationGraph

from cct.cct import CCT, cct  # type: ignore
from cct.util import namespaces, graph, WF, TOOLS  # type: ignore


print("Preparing queries...", file=stderr)

"""
A query to obtain all steps of a workflow and the relevant in- and outputs.
"""
query_steps = sparql.prepareQuery(
    """
    SELECT
        ?step ?tool
        ?output ?is_final_output
        ?x1 ?x2 ?x3
    WHERE {
        ?wf wf:edge ?step.
        ?step wf:applicationOf ?tool.

        # What are the inputs?
        OPTIONAL { ?step wf:input1 ?x1. }
        OPTIONAL { ?step wf:input2 ?x2. }
        OPTIONAL { ?step wf:input3 ?x3. }

        # Is this the final step?
        ?step wf:output ?output.
        OPTIONAL {
            { ?next_step wf:input1 ?output }
            UNION
            { ?next_step wf:input2 ?output }
            UNION
            { ?next_step wf:input3 ?output }.
        }
        BIND (!bound(?next_step) AS ?is_final_output).
    }
    """, initNs=namespaces)


def workflow_expr(workflows: Graph, tools: Graph, workflow: Node) -> Graph:
    """
    Concatenate workflow expressions and add them to a graph.
    """

    # Find expressions for each step by mapping the output node of each to the
    # algebra expression associated with the tool, and the input nodes
    steps: dict[Node, tuple[Expr, list[Node]]] = {}
    for node in workflows.query(query_steps, initBindings={"wf": workflow}):
        expr_string = tools.value(
            node.tool, TOOLS.algebraexpression, any=False)
        assert expr_string, f"{node.tool} has no algebra expression"
        expr = cct.parse(expr_string).primitive()
        inputs = [x for x in (node.x1, node.x2, node.x3) if x]
        steps[node.output] = expr, inputs

    sources = set(workflows.objects(subject=workflow, predicate=WF.source))

    output = TransformationGraph(cct, CCT)
    output.add_workflow(workflow, sources, steps)
    return output


cct_graph = TransformationGraph.vocabulary(cct, CCT)

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

        fn = basename(workflow_file)
        with open(f"wf_{fn}.dot", 'w') as f:
            rdf2dot(g, f)
        g.serialize(format="ttl", destination=f"wf_{fn}.ttl", encoding='utf-8')
