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
from quangis.cct import cct
from typing import Mapping, Iterator, TextIO

ROOT = Path(__file__).parent.parent
BUILD_DIR = ROOT / "build"

tools = Graph()
tools.parse(ROOT / "data" / "tools" / "abstract.ttl")

def write_csv_summary(handle: TextIO,
        expect: Mapping[URIRef, set[URIRef]],
        actual: Mapping[URIRef, set[URIRef]],
        workflows: set[URIRef]) -> None:
    """Create a summary CSV by providing a mapping from tasks to expected and 
    actual workflows that match it."""

    tasks = set(expect.keys())

    assert all(wf in workflows for wfs in expect.values() for wf in wfs)
    assert all(wf in workflows for wfs in actual.values() for wf in wfs)
    assert tasks == set(actual.keys())

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
    g += wg
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


def upload(workflow_paths: list[Path], store: TransformationStore,
        **kwargs) -> set[URIRef]:
    workflows = set()
    for wf_path in workflow_paths:
        g = read_transformation(wf_path, **kwargs)
        assert g.uri
        workflows.add(g.uri)
        store.put(g)
    return workflows


def query(task_paths: list[Path], store: TransformationStore, **kwargs) \
        -> tuple[dict[URIRef, set[URIRef]], dict[URIRef, set[URIRef]]]:
    actual: dict[URIRef, set[URIRef]] = dict()
    expect: dict[URIRef, set[URIRef]] = dict()
    for task_path in task_paths:
        query = read_query(task_path, **kwargs)
        root = query.root
        actual[root] = store.run(query)  # type: ignore
        expect[root] = set(
            query.graph.objects(root, TF.implementation))  # type: ignore
        print(f"Results: {', '.join(str(wf) for wf in actual[root])}")
    return actual, expect
