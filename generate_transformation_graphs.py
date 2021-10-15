#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

import os.path
from glob import glob
from sys import stderr
from transformation_algebra.rdf import TransformationGraph

from cct import CCT, cct  # type: ignore
from util import write_graph, graph  # type: ignore
from workflow import Workflow


tools = graph("TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl")

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    try:
        print(f"\nWorkflow {workflow_file}", file=stderr)
        workflow = Workflow(workflow_file, tools)
        g = TransformationGraph(cct, CCT)
        g.add_workflow(workflow.root, workflow.sources, workflow.format())
    except Exception as e:
        print("Failure: ", e, file=stderr)
    else:
        print("Success!", file=stderr)
        write_graph(g, os.path.splitext(os.path.basename(workflow_file))[0])
