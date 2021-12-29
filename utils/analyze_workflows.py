#!/usr/bin/env python3
"""
This file generates a textual analysis of each workflow.
"""

from __future__ import annotations

from sys import stderr
import itertools
from collections import defaultdict
from rdflib.term import Node  # type: ignore

from config import build_path, workflow_paths  # type: ignore
from cct import cct  # type: ignore
from workflow import Workflow  # type: ignore


for wf_path in workflow_paths:
    try:
        path = build_path / (wf_path.stem + ".txt")
        print('Building', path.name, file=stderr)
        wf = Workflow(wf_path)

        counter = itertools.count(start=1)
        label: dict[Node, int] = defaultdict(lambda: next(counter))

        with open(path, 'w') as f:
            print("SOURCES:", [label[i] for i in wf.sources], file=f)
            for out in wf.outputs:
                print(file=f)
                print("TOOL:", wf.tools[out], file=f)
                print("OUTPUT:", label[out], file=f)
                print("INPUTS:", [label[i] for i in wf.inputs[out]], file=f)
                print("EXPRESSION:", wf.expressions[out], file=f)
                print("PRIMITIVE:",
                    cct.parse(wf.expressions[out]).primitive(), file=f)
    except Exception as e:
        print("Failure: ", e)
    else:
        print("Success.")
    print()
