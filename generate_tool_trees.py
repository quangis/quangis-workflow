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
from util import graph, Labeller, TOOLS  # type: ignore
from workflow import Workflow


tools = graph("TheoryofGISFunctions/ToolDescription_TransformationAlgebra.ttl")

with open("build/tools.txt", 'w') as f:
    for tool, expr in tools[:TOOLS.algebraexpression:]:
        print(tool, file=f)
        print(cct.parse(expr).tree(), file=f)
        print(file=f)
