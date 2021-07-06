#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

import rdflib  # type: ignore
from rdflib import Graph, URIRef
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql
from glob import glob
from sys import stderr

from transformation_algebra.expr import Expr
from cct import cct, R1, R2, R3, Obj, Reg, Loc, Ratio, apply, groupby, ratio, \
    size, pi1

from typing import List, Tuple, Optional, Dict, Union

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
GIS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
WF = rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")


def graph(*gs: Union[str, Graph]) -> rdflib.Graph:
    graph = rdflib.Graph()
    for g in gs:
        if isinstance(g, str):
            graph.parse(g, format=rdflib.util.guess_format(g))
        else:
            assert isinstance(g, Graph)
            graph += g
    return graph


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
    """,
    initNs={"wf": WF, "tools": TOOLS}
)

"""
A query to obtain all workflows and their descriptions.
"""
query_workflow = sparql.prepareQuery(
    """
    SELECT
        ?node ?description
    WHERE {
        ?node a wf:Workflow.
        ?node rdfs:comment ?description.
    } GROUP BY ?node
    """,
    initNs={"wf": WF, "rdfs": RDFS}
)


def workflow_expr(g: Graph, workflow: Node) -> None:
    """
    Concatenate workflow expressions and add them to the graph.
    """

    # Finding the individual expressions for each step:
    # Map the output node of every workflow step to the tool, the associated
    # algebra expression, and the nodes from which it gets its input
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


# Produce workflow repository with representation of transformations.
g = graph(
    cct.vocabulary(),
    "workflows/ToolDescription_TransformationAlgebra.ttl",
    *glob("workflows/**/*_cct.ttl"))


for i, workflow in enumerate(g.query(query_workflow), start=1):
    try:
        print(f"\nWorkflow {i}: {workflow.description}", file=stderr)
        workflow_expr(g, workflow.node)
    except Exception as e:
        print("FAILURE: ", e, file=stderr)
    else:
        print("SUCCESS.", file=stderr)

print(g.serialize(format="ttl").decode("utf-8"))

exit()


print("\nTrying to query!")


# Try workflow 1
flow = (
    R3(Obj, Reg, Ratio) << ... << apply << ... << (
        ratio &
        groupby << ... << (size & pi1) &
        apply << ... << (size & R2(Obj, Reg))
    )
)
flow1 = R3(Obj, Reg, Ratio)

for result in cct.query(g, flow):
    print(result.description)
