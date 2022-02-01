#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

from sys import stderr
from transformation_algebra import TransformationGraph

from config import build_path, workflow_paths  # type: ignore
from cct import cct  # type: ignore
from workflow import Workflow  # type: ignore

vocab = TransformationGraph(cct)
vocab.add_vocabulary()
vocab.serialize(build_path / "cct.ttl", format='ttl', encoding='utf-8')

for wf_path in workflow_paths:
    try:
        path = build_path / (wf_path.stem + ".ttl")
        print("Building", path.name, file=stderr)
        wf = Workflow(wf_path)
        g = TransformationGraph(cct, with_noncanonical_types=False)
        g.add_workflow(wf.root, wf.wf, wf.sources)
        g.serialize(path, format='ttl', encoding='utf-8')
    except Exception as e:
        print("Failure: ", e, file=stderr)
    else:
        print("Success!", file=stderr)
    print()
