#!/usr/bin/env python3
"""
This file generates files that should help debug problems.

-   A GraphViz graph of the CCT vocabulary.
-   A textual analysis of each workflow.
-   Two GraphViz graphs of each workflow: one where primitives have been
    expanded and one where they haven't.
"""

from __future__ import annotations

from sys import stderr
import itertools
from pathlib import Path
from collections import defaultdict
from rdflib.term import Node, Literal  # type: ignore
from rdflib.namespace import RDFS  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from transformation_algebra.graph import TransformationGraph

from config import build_path, workflow_paths, WF, TOOLS  # type: ignore
from cct import cct  # type: ignore
from workflow import Workflow  # type: ignore


def write_taxonomy(path: Path):
    print('Building', path.name, file=stderr)
    vocab = TransformationGraph(cct, minimal=True, with_labels=True)
    vocab.add_taxonomy()
    with open(path, 'w') as f:
        rdf2dot(vocab, f)


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
            # print("PRIMITIVE:",
            #     cct.parse(wf.expressions[out]).primitive(), file=f)


def write_graph(wf: Workflow, path: Path, primitive: bool = False):

    assert not primitive

    print('Building', path.name, file=stderr)
    g = TransformationGraph(cct, minimal=True, with_labels=True)
    step2expr = g.add_workflow(wf.root, wf.wf, wf.sources)

    # Annotate the expression nodes that correspond with output nodes of a tool
    # with said tool
    for output, tool in wf.tools.items():
        g.add((step2expr[output], RDFS.comment, Literal(
            "using " + tool[len(TOOLS):]
        )))
    for output, comment in wf.comment.items():
        g.add((step2expr[output], RDFS.comment, Literal(comment)))

    g.add((step2expr[wf.output], RDFS.comment, Literal("output")))

    with open(path, 'w') as f:
        rdf2dot(g, f)


write_taxonomy(build_path / "cct_taxonomy.dot")
for path in workflow_paths:
    try:
        wf = Workflow(path)
        write_tools_text(wf, build_path / (path.stem + ".txt"))
        write_graph(wf, build_path / (path.stem + ".raw.dot"))
        # write_graph(wf, build_path / (path.stem + ".prim.dot"), primitive=True)
    except Exception as e:
        print("Failure: ", e)
        raise
    else:
        print("Success.")
    print()
