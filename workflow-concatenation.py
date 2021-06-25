#!/usr/bin/env python3
"""
This is a test file for workflow concatenation. Final product will be
different.
"""

from __future__ import annotations

import rdflib  # type: ignore
from rdflib import Graph
from rdflib.term import Node  # type: ignore
from rdflib.plugins import sparql
from glob import glob

from transformation_algebra.expr import Expr
from cct import cct

from typing import List, Tuple, Optional, Dict

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
        ?current_step_output ?is_final_output
        ?expression
        ?x1 ?x2 ?x3
    WHERE {
        ?wf a wf:Workflow.
        ?wf wf:edge ?step.
        ?step wf:output ?current_step_output.

        # What is the algebra expression for this step?
        ?step wf:applicationOf ?tool.
        ?tool tools:algebraexpression ?expression.

        # What are the inputs?
        OPTIONAL { ?step wf:input1 ?x1. }
        OPTIONAL { ?step wf:input2 ?x2. }
        OPTIONAL { ?step wf:input3 ?x3. }

        # Is this the final step?
        OPTIONAL {
            { ?next_step wf:input1 ?current_step_output }
            UNION
            { ?next_step wf:input2 ?current_step_output }
            UNION
            { ?next_step wf:input3 ?current_step_output }.
        }
        BIND (!bound(?next_step) AS ?is_final_output).
    }
    """,
    initNs={"wf": WF, "tools": TOOLS}
)


def construct(g: Graph, workflow: Node) -> None:
    """
    Concatenate workflow expressions and add them to the graph.
    """
    description = next(g.objects(subject=workflow, predicate=RDFS.comment))

    print()
    print("Current workflow: ", description)

    # Set of nodes representing source data
    sources = set(g.objects(subject=workflow, predicate=WF.source))

    # Map every step to its algebra expression and the source nodes/steps it
    # gets its inputs from
    step_info: Dict[Node, Tuple[Expr, List[Node]]] = dict()
    output_node: Optional[Node] = None
    steps = g.query(query_steps, initBindings={"wf": workflow})

    for step in steps:
        current = step.current_step_output

        # Set the output node if we happen to chance upon it
        if step.is_final_output:
            assert not output_node, "multiple output nodes?"
            output_node = current

        expr = cct.parse(step.expression)
        inputs = [x for x in (step.x1, step.x2, step.x3) if x]

        step_info[current] = (expr, inputs)

    assert output_node

    stack = [output_node]
    while stack:
        current = stack.pop()
        if current in step_info:
            expr, inputs = step_info[current]
            print(expr.type)
            print(inputs)
            stack.extend(inputs)
        else:
            assert current in sources, str(current)
            print(current)


# Produce all workflows
for workflow in g.subjects(predicate=RDF.type, object=WF.Workflow):
    construct(g, workflow)
