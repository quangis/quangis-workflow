#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

import os.path
from glob import glob
from sys import stderr
from transformation_algebra import TransformationGraph

from cct import CCT, cct  # type: ignore
from util import graph, Labeller  # type: ignore
from workflow import Workflow


tools = graph("TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl")

for workflow_file in glob("TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    try:
        workflow = Workflow(workflow_file, tools)
        name = os.path.splitext(os.path.basename(workflow_file))[0]
        print(name)
        label = Labeller()
        with open(f"build/{name}.txt", 'w') as f:
            print("SOURCES:", [label[i] for i in workflow.sources], file=f)
            for out in workflow.outputs:
                print(file=f)
                print("TOOL:", workflow.tools[out], file=f)
                print("OUTPUT:", label[out], file=f)
                print("INPUTS:", [label[i] for i in workflow.inputs[out]], file=f)
                print("EXPRESSION:", workflow.expressions[out], file=f)
                print("PRIMITIVE:",
                    cct.parse(workflow.expressions[out]).primitive(), file=f)
    except Exception as e:
        print("Failure: ", e)
    else:
        print("Success.")
    print()
