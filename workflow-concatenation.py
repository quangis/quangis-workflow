#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

import rdflib  # type: ignore
from rdflib import Graph, BNode, URIRef
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql
from glob import glob

from transformation_algebra.expr import Expr
from cct import cct

from typing import List, Tuple, Optional, Dict, Union

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
GIS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
WF = rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")


def graph(*paths: str) -> rdflib.Graph:
    g = rdflib.Graph()
    for path in paths:
        g.parse(path, format=rdflib.util.guess_format(path))
    return g


g = graph(
    "workflows/ToolDescription_TransformationAlgebra.ttl",
    *glob("workflows/**/*_cct.ttl"))


"""
A query to obtain all steps of a workflow and the relevant in- and outputs.
"""
query_steps = sparql.prepareQuery(
    """
    SELECT
        ?wf
        ?tool
        ?output ?is_final_output
        ?expression
        ?x1 ?x2 ?x3
    WHERE {
        ?wf a wf:Workflow.
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


def workflow_expr(g: Graph, workflow: Node) -> None:
    """
    Concatenate workflow expressions and add them to the graph.
    """
    description = next(g.objects(subject=workflow, predicate=RDFS.comment))

    print()
    print("Current workflow: ", description)

    # Finding the individual expressions for each step:
    # Map the output node of every workflow step to the tool, the associated
    # algebra expression, and the nodes from which it gets its input
    step_info: Dict[Node, Tuple[str, Expr, List[Node]]] = dict()
    final_output: Optional[Node] = None
    for step in g.query(query_steps, initBindings={"wf": workflow}):
        assert step.expression, f"{step.tool} has no algebra expression"
        expr = cct.parse(step.expression)
        inputs = [x for x in (step.x1, step.x2, step.x3) if x]
        step_info[step.output] = step.tool, expr, inputs

        if step.is_final_output:
            assert not final_output, f"{step.tool} has multiple final nodes"
            final_output = step.output
    assert final_output, "workflow has no output node"

    # Combining the expressions in RDF format:
    # Map the output node of every workflow step to the output node of an
    # RDF-encoded algebra expression
    root = BNode()
    sources = set(g.objects(subject=workflow, predicate=WF.source))
    cache: Dict[Node, Node] = dict()

    def f(node: Node) -> Union[URIRef, Tuple[Node, Expr]]:
        if node in sources:
            return node
        tool, expr, inputs = step_info[node]
        if node not in cache:
            bindings = {f"x{i}": f(x) for i, x in enumerate(inputs, start=1)}
            try:
                cache[node] = cct.rdf_expr(g, root, expr, bindings)
            except RuntimeError as e:
                raise RuntimeError(f"While converting tool {tool}: {e}") from e
        return cache[node], expr

    f(final_output)


# Produce all workflows
for workflow in g.subjects(predicate=RDF.type, object=WF.Workflow):
    try:
        workflow_expr(g, workflow)
    except Exception as e:
        print("FAILURE: ", e)
