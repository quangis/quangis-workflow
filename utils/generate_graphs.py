#!/usr/bin/env python3
"""
This file generates transformation graphs for entire workflows, concatenating
the algebra expressions for each individual use of a tool.
"""

from __future__ import annotations

from sys import stderr
from transformation_algebra import TransformationGraph
from transformation_algebra.expr import SourceError
from rdflib.namespace import RDFS  # type: ignore

from config import build_path, workflow_paths  # type: ignore
from cct import cct  # type: ignore
from workflow import Workflow  # type: ignore


for wf_path in workflow_paths:
    try:
        path = build_path / (wf_path.stem + ".ttl")
        print("Building", path.name, file=stderr)
        wf = Workflow(wf_path)

        node2expr = {
            node: cct.parse(expr).primitive()
            for node, expr in wf.expressions.items()
        }

        g = TransformationGraph(cct)
        g.add((wf.root, RDFS.comment, wf.description))
        g.add_workflow(wf.root, {
            node2expr[output]: list(node2expr.get(i, i) for i in inputs)
            for output, inputs in wf.inputs.items()
        })
        g.serialize(path, format='ttl', encoding='utf-8')
    except SourceError as e:
        expr2node = {v: k for k, v in node2expr.items()}
        print("Failure while attaching the output of tool",
            wf.tools[expr2node[e.attachment]], "!",
            e, file=stderr)
    except Exception as e:
        print("Failure: ", e, file=stderr)
    else:
        print("Success!", file=stderr)
    print()
