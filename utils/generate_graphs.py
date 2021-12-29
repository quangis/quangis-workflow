#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

from sys import stderr
from rdflib.namespace import RDFS
from transformation_algebra import TransformationGraph
from transformation_algebra.expr import SourceError

from config import root_path, build_path
from cct import cct  # type: ignore
from workflow import Workflow


for scenario_path in root_path.glob(
        "TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    try:
        print(f"\nWorkflow {scenario_path.name}", file=stderr)
        workflow = Workflow(scenario_path)

        node2expr = {
            node: cct.parse(expr).primitive()
            for node, expr in workflow.expressions.items()
        }

        g = TransformationGraph(cct)
        g.add((workflow.root, RDFS.comment, workflow.description))
        g.add_workflow(workflow.root, {
            node2expr[output]: list(node2expr.get(i, i) for i in inputs)
            for output, inputs in workflow.inputs.items()
        })
    except SourceError as e:
        expr2node = {v: k for k, v in node2expr.items()}
        print("Failure while attaching the output of tool",
            workflow.tools[expr2node[e.attachment]], "!",
            e, file=stderr)
    except Exception as e:
        print("Failure: ", e, file=stderr)
    else:
        print("Success!", file=stderr)

        g.serialize(build_path / (scenario_path.stem + ".graph.ttl"),
            format='ttl', encoding='utf-8')
