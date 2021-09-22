#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

from rdflib import Graph, URIRef  # type: ignore
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from glob import glob
from sys import stderr
from os.path import basename

from transformation_algebra.expr import Expr
from transformation_algebra.rdf import TA

from cct import cct, R2, R3a, Obj, Reg, Ratio, \
    lTopo, apply, ratio, groupby, size, pi1
from cct.util import namespaces, graph, WF, TOOLS, dot, ttl

from typing import List, Tuple, Optional, Dict, Union


print("Preparing queries...", file=stderr)

"""
A query to obtain all workflows and their descriptions.
"""
query_workflow = sparql.prepareQuery(
    """
    SELECT
        ?node ?description ?output
    WHERE {
        ?node a wf:Workflow.
        ?node rdfs:comment ?description.
        OPTIONAL {
            ?node ta:target/ta:type/rdfs:label ?output.
        }
    } GROUP BY ?node
    """, initNs=namespaces)


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


"""
A query to obtain all operations in a workflow.
"""
query_operations = sparql.prepareQuery(
    """
    SELECT
        (group_concat(?input; separator=", ") as ?inputs)
        ?operation
        (group_concat(?output; separator=", ") as ?outputs)
    WHERE {
        ?wf a wf:Workflow, ta:Transformation.
        ?wf ta:operation ?op.
        ?op rdf:type/rdfs:label ?operation.
        ?op ta:input/ta:type/rdfs:label ?input.
        ?op ta:output ?out.
        ?out ta:type/rdfs:label ?output.
    } GROUP BY ?op ?out
    """, initNs=namespaces)


def workflow_expr(workflows: Graph, tools: Graph, workflow: Node) -> Graph:
    """
    Concatenate workflow expressions and add them to a graph.

    """
    output = Graph()

    # Find expressions for each step by mapping the output node of each to the
    # algebra expression associated with the tool, and the input nodes
    steps: dict[Node, tuple[Expr, list[Node]]] = {}
    for node in workflows.query(query_steps, initBindings={"wf": workflow}):
        expr_string: Optional[str] = tools.value(subject=node.tool,
            predicate=TOOLS.algebraexpression, any=False)
        assert expr_string, f"{node.tool} has no algebra expression"
        expr = cct.parse(expr_string).primitive()
        inputs = [x for x in (node.x1, node.x2, node.x3) if x]
        steps[node.output] = expr, inputs

    sources = set(workflows.objects(subject=workflow, predicate=WF.source))

    cct.rdf_workflow(output, workflow, sources, steps)
    return output


cct_graph = cct.vocabulary()
tool_graph = graph(
    "TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl"
)

full_graph = cct_graph + tool_graph

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    if "Amsterdam" not in workflow_file:
        continue
    print(f"\nWorkflow {workflow_file}", file=stderr)
    workflow_graph = graph(workflow_file)
    full_graph += workflow_graph
    workflows = workflow_graph.query(query_workflow)
    for i, workflow in enumerate(workflows):
        print(workflow.description, file=stderr)
        try:
            g = workflow_expr(workflow_graph, tool_graph, workflow.node)

            with open(f"wf_{basename(workflow_file)}{i}.dot", 'w') as f:
                rdf2dot(g, f)

            full_graph += g
            # print(dot(g))
        except Exception as e:
            print("FAILURE: ", e, file=stderr)
            raise
        else:
            print("SUCCESS.", file=stderr)


# for workflow in g.query(query_workflow):
#     if "Amsterdam" not in workflow.description:
#         continue
#     print(f"\nWorkflow: {workflow.description}")
#     print(f"Final output: {workflow.output}")
#     for node in g.query(query_operations, initBindings={"wf": workflow.node}):
#         print("Operation:", node.operation)
#         print("Input:", node.inputs)
#         print("Outputs:", node.outputs, "\n")


# exit()
# g.serialize(format="ttl", destination='everything.ttl', encoding='utf-8')

# for result in g.query(query_output_types):
#     print(result.description, result.op, result.params)
#     print(result.operations)

# exit()

# Try workflow 1
flow = R3a(Obj, Reg, Ratio) << ... << apply << ... << size

# flow = R3a(Obj, Reg, Ratio) << ... << apply << ... << (
#     ratio &
#     groupby << ... << (size & pi1) &
#     apply << ... << (size & R2(Obj, Reg))
# )

for result in cct.query(full_graph, flow):
    print("Result:", result.description)
