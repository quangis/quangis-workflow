#!/usr/bin/env python3
"""
This file generates a textual analysis of each workflow, as well as a
simplified graph.
"""

from __future__ import annotations

from sys import stderr
import itertools
from pathlib import Path
from collections import defaultdict
from rdflib.term import Node  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from transformation_algebra.graph import TransformationGraph

from config import build_path, workflow_paths  # type: ignore
from cct import cct  # type: ignore
from workflow import Workflow  # type: ignore


def write_tools_text(wf: Workflow, path: Path):
    counter = itertools.count(start=1)
    label: dict[Node, int] = defaultdict(lambda: next(counter))

    print('Building', path.name, file=stderr)
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


def write_graph(wf: Workflow, path: Path, primitive: bool = False):
    print('Building', path.name, file=stderr)
    node2expr = {
        node: cct.parse(expr).primitive() if primitive else cct.parse(expr)
        for node, expr in wf.expressions.items()
    }
    g = TransformationGraph(cct, minimal=True, with_labels=True)
    g.add_workflow(wf.root, {
        node2expr[output]: list(node2expr.get(i, i) for i in inputs)
        for output, inputs in wf.inputs.items()
    })
    with open(path, 'w') as f:
        rdf2dot(g, f)


for path in workflow_paths:
    try:
        wf = Workflow(path)
        write_tools_text(wf, build_path / (path.stem + ".txt"))
        write_graph(wf, build_path / (path.stem + ".raw.dot"))
        write_graph(wf, build_path / (path.stem + ".prim.dot"), primitive=True)
    except Exception as e:
        print("Failure: ", e)
    else:
        print("Success.")
    print()
