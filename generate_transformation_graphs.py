#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

import os.path
from glob import glob
from sys import stderr
from rdflib.namespace import RDFS
from transformation_algebra import TransformationGraph
from transformation_algebra.expr import SourceError

from cct import CCT, cct  # type: ignore
from util import write_graph, graph  # type: ignore
from workflow import Workflow


tools = graph("TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl")

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    try:
        print(f"\nWorkflow {workflow_file}", file=stderr)
        workflow = Workflow(workflow_file, tools)
        g = TransformationGraph(cct)

        node2expr = {
            node: cct.parse(expr).primitive()
            for node, expr in workflow.expressions.items()
        }

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
        write_graph(g, os.path.splitext(os.path.basename(workflow_file))[0])
