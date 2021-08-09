#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

from rdflib import Graph, URIRef  # type: ignore
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql  # type: ignore
from glob import glob
from sys import stderr

from transformation_algebra.expr import Expr
from transformation_algebra.rdf import TA

from cct.util import namespaces, graph, WF
from cct import cct, R3a, Obj, Reg, Ratio, lTopo

from typing import List, Tuple, Optional, Dict, Union


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
        ?tool ?expression
        ?output ?is_final_output
        ?x1 ?x2 ?x3
    WHERE {
        ?wf wf:edge ?step.
        ?step wf:output ?output.

        # What is the algebra expression for this step?
        ?step wf:applicationOf ?tool.
        OPTIONAL { ?tool tools:algebraexpression ?expression. }

        # What are the inputs?
        OPTIONAL { ?step wf:input1 ?x1. }
        OPTIONAL { ?step wf:input2 ?x2. }
        OPTIONAL { ?step wf:input3 ?x3. }

        # Is this the final step?
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


def workflow_expr(g: Graph, workflow: Node) -> None:
    """
    Concatenate workflow expressions and add them to the graph.
    """

    # Finding the individual expressions for each step:
    # Map the output node of every workflow step to the tool it uses, the
    # algebra expression associated to the tool, and the nodes from which it
    # gets its input
    step_info: Dict[Node, Tuple[str, Expr, List[Node]]] = dict()
    final_output: Optional[Node] = None
    for step in g.query(query_steps, initBindings={"wf": workflow}):
        assert step.expression, f"{step.tool} has no algebra expression"
        expr = cct.parse(step.expression).primitive()
        inputs = [x for x in (step.x1, step.x2, step.x3) if x]
        step_info[step.output] = step.tool, expr, inputs

        if step.is_final_output:
            assert not final_output, f"{step.tool} has multiple final nodes"
            final_output = step.output
    assert final_output, "workflow has no output node"

    # Combining the expressions in RDF format:
    # Map the output node of every workflow step to the output node of an
    # RDF-encoded algebra expression
    sources = set(g.objects(subject=workflow, predicate=WF.source))
    cache: Dict[Node, Node] = dict()

    def f(node: Node) -> Union[URIRef, Tuple[Node, Expr]]:
        if node in sources:
            return node
        tool, expr, inputs = step_info[node]
        if node not in cache:
            bindings = {f"x{i}": f(x) for i, x in enumerate(inputs, start=1)}
            try:
                cache[node] = cct.rdf_expr(g, workflow, expr, bindings)
            except RuntimeError as e:
                raise RuntimeError(f"In {tool}: {e}") from e
        return cache[node], expr

    f(final_output)
    g.add((workflow, TA.target, cache[final_output]))


# Produce workflow repository with representation of transformations.
g = graph(
    cct.vocabulary(),
    "TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl",
    *glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"))


for i, workflow in enumerate(g.query(query_workflow), start=1):
    try:
        print(f"\nWorkflow {i}: {workflow.description}", file=stderr)
        workflow_expr(g, workflow.node)
    except Exception as e:
        print("FAILURE: ", e, file=stderr)
    else:
        print("SUCCESS.", file=stderr)

for workflow in g.query(query_workflow):
    if "Amsterdam" not in workflow.description:
        continue
    print(f"\nWorkflow: {workflow.description}")
    print(f"Final output: {workflow.output}")
    for node in g.query(query_operations, initBindings={"wf": workflow.node}):
        print("Operation:", node.operation)
        print("Input:", node.inputs)
        print("Outputs:", node.outputs, "\n")

# g.serialize(format="ttl", destination='everything.ttl', encoding='utf-8')

exit()


# for result in g.query(query_output_types):
#     print(result.description, result.op, result.params)
#     print(result.operations)

# exit()

# Try workflow 1
# flow = (
#     R3a(Obj, Reg, Ratio) << ... << apply << ... << (
#         ratio &
#         groupby << ... << (size & pi1) &
#         apply << ... << (size & R2(Obj, Reg))
#     )
# )
flow = (
    R3a(Obj, Reg, Ratio) << ... << lTopo
)

for result in cct.query(g, flow):
    print(result.description)
