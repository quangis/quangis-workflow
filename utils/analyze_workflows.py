#!/usr/bin/env python3
"""
This file generates a textual analysis of each workflow.
"""

from __future__ import annotations

import os.path
import itertools
from collections import defaultdict
from rdflib.term import Node

from config import root_path, build_path
from cct import cct  # type: ignore
from workflow import Workflow


for workflow_file in root_path.glob(
        "TheoryofGISFunctions/Scenarios/**/*_cct.ttl"):
    try:
        workflow = Workflow(workflow_file)
        name = os.path.splitext(os.path.basename(workflow_file))[0]
        print(name)

        counter = itertools.count(start=1)
        label: dict[Node, int] = defaultdict(lambda: next(counter))

        with open(build_path / (name + ".txt"), 'w') as f:
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
