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
from util import graph, Labeller  # type: ignore
from workflow import Workflow


tools = graph("TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl")

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    workflow = Workflow(workflow_file, tools)
    name = os.path.splitext(os.path.basename(workflow_file))[0]

    label = Labeller()
    print("".join('*' for _ in range(79)))
    print(workflow.file)
    print("SOURCES:", [label[i] for i in workflow.sources])
    print("".join('.' for _ in range(79)))
    for out in workflow.outputs:
        print("TOOL:", workflow.tools[out])
        print("OUTPUT:", label[out])
        print("INPUTS:", [label[i] for i in workflow.inputs[out]])
        print("EXPRESSION:", workflow.expressions[out])
        print("PRIMITIVE:",
            cct.parse(workflow.expressions[out]).primitive())
        print()
