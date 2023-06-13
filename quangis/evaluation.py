#!/usr/bin/env python3
# Sends transformation graphs for all workflows to a graph store, and
# subsequently fires queries for all tasks to retrieve them back.

from __future__ import annotations

import csv
from itertools import product
from pathlib import Path
from rdflib.graph import Graph
from rdflib.term import URIRef
from rdflib.util import guess_format

from transforge.graph import TransformationGraph
from transforge.query import TransformationQuery
from transforge.namespace import TF, shorten
from transforge.workflow import WorkflowGraph
from transforge.util.store import TransformationStore
from cct import cct
from typing import Mapping, Iterator, TextIO


# STORE_URL = "https://localhost:3030"
# STORE_USER = None
STORE_URL = "http://192.168.56.1:8000"
STORE_USER = ("user", "password")

ROOT = Path(__file__).parent
BUILD_DIR = ROOT / "build"

tools = Graph()
tools.parse(ROOT / "data" / "all.ttl")

def write_csv_summary(handle: TextIO,
        workflows: set[URIRef],
        tasks: set[URIRef],
        expect: Mapping[URIRef, set[URIRef]],
        actual: Mapping[URIRef, set[URIRef]]) -> None:
    """Create a summary CSV by providing a mapping from tasks to expected and 
    actual workflows that match it."""

    assert all(wf in workflows for wf in actual.keys())
    assert all(wf in workflows for wf in expect.keys())
    assert all(wf in expect and wf in actual for wf in workflows)
    assert all(t in tasks for t in expect.values())
    assert all(t in tasks for t in actual.values())

    n_tpos, n_tneg, n_fpos, n_fneg = 0, 0, 0, 0
    header = ["Task", "Precision", "Recall"] + sorted(
        shorten(wf) for wf in workflows)
    w = csv.DictWriter(handle, fieldnames=header)
    w.writeheader()
    for task in sorted(tasks):
        expectwfs, actualwfs = expect[task], actual[task]
        n_fpos += len(actualwfs - expectwfs)
        n_fneg += len(expectwfs - actualwfs)
        n_tpos += len(actualwfs.intersection(expectwfs))
        n_tneg += len(workflows - expectwfs - actualwfs)
        row = dict({
            shorten(wf):
                ('●' if wf in actualwfs else '○') +
                ("⨯" if (wf in actualwfs) ^ (wf in expectwfs) else "")
            for wf in workflows},
            Task=shorten(task))
        w.writerow(row)

    try:
        w.writerow({
            "Precision": "{0:.3f}".format(n_tpos / (n_tpos + n_fpos)),
            "Recall": "{0:.3f}".format(n_tpos / (n_tpos + n_fneg))
        })
    except ZeroDivisionError:
        w.writerow({"Precision": "?", "Recall": "?"})


def read_transformation(wf_path: Path,
        format: str | None = None, **kwargs) -> TransformationGraph:
    """Read a single workflow into a transformation graph."""
    wg = WorkflowGraph(cct, tools)
    wg.parse(wf_path, format=format or guess_format(str(wf_path)))
    wg.refresh()
    g = TransformationGraph(cct, **kwargs)
    g.add_workflow(wg)
    return g


def read_query(task_path: Path,
        format: str | None = None, **kwargs) -> TransformationQuery:
    """Read a single task into a transformation query."""
    qg = Graph()
    qg.parse(task_path, format=format or guess_format(str(task_path)))
    query = TransformationQuery(cct, qg, **kwargs)
    return query

def variants() -> Iterator[tuple[str, dict, dict]]:
    """Parameters for the workflow and task graphs in order to run different 
    variants of the experiment."""
    opacities = ('workflow', 'tool', 'internal')
    passthroughs = ('pass', 'block')
    orderings = ('unordered', 'ordered')
    for variant in product(opacities, passthroughs, orderings):
        opacity, passthrough, ordering = variant
        if ordering == 'ordered' and opacity == 'workflow':
            continue

        name = "-".join(variant)
        kwargsg = dict(
            passthrough=(passthrough == 'pass'),
            with_intermediate_types=(opacity == 'internal'))
        kwargsq = dict(
            by_types=(opacity != 'workflow'),
            by_chronology=(ordering == 'ordered' and
                opacity != 'workflow'),
            unfold_tree=True)
        yield name, kwargsg, kwargsq


def write_evaluations(store: TransformationStore,
        task_paths=ROOT.glob("tasks/*.ttl"),
        workflow_paths=ROOT.glob("workflows/*.ttl")) -> None:

    task_paths = list(task_paths)
    workflow_paths = list(workflow_paths)

    for variant, kwargsg, kwargsq in variants():
        print("Variant:", variant)

        # Build & send transformation graphs for every workflow
        workflows: set[URIRef] = set()
        for wf_path in workflow_paths:
            print(f"Building graph for workflow {wf_path}...")
            g = read_transformation(wf_path, **kwargsg)
            assert g.uri
            workflows.add(g.uri)
            print("Sending transformation graph to graph store...")
            store.put(g)

        # Fire query for every task
        tasks: set[URIRef] = set()
        actual: dict[URIRef, set[URIRef]] = dict()
        expect: dict[URIRef, set[URIRef]] = dict()
        for task_path in task_paths:
            print(f"Reading transformation graph for task {task_path}...")
            query = read_query(task_path, **kwargsq)
            root = query.root
            tasks.add(root)

            print("Querying graph store...")
            actual[root] = store.run(query)  # type: ignore
            expect[root] = set(
                query.graph.objects(root, TF.implementation))  # type: ignore
            print(f"Results: {', '.join(str(wf) for wf in actual[root])}")

        (BUILD_DIR / "eval").mkdir(exist_ok=True)
        with open(BUILD_DIR / f"{variant}.csv") as f:
            write_csv_summary(f, workflows, tasks, expect, actual)


if __name__ == '__main__':
    store = TransformationStore.backend('marklogic', STORE_URL,
        cred=STORE_USER)
    write_evaluations(store)
