#!/usr/bin/env python3
# Sends transformation graphs for all workflows to a graph store, and
# subsequently fires queries for all tasks to retrieve them back.

from __future__ import annotations

import csv
from itertools import chain, product
from pathlib import Path
from rdflib.term import Node

from transforge import TransformationQuery
from transforge.namespace import TA, EX
from transforge.util.store import TransformationStore
from transforge.util.common import (graph, build_transformation)
from cct.language import cct

STORE_TYPE = "fuseki"
STORE_URL = "https://localhost:3030"
STORE_USER = None
# STORE_TYPE = "marklogic"
# STORE_URL = "http://localhost:8000"
# STORE_USER = ("user", "password")

ROOT = Path(__file__).parent
BUILD_DIR = ROOT / "build"


def summary_csv(path: Path | str,
        table_expected: dict[str, set[Node]],
        table_actual: dict[str, set[Node]]) -> None:

    tasks = set(table_expected.keys())
    workflows = set.union(*chain(table_expected.values(),
        table_actual.values()))

    header = ["Task", "Precision", "Recall"] + sorted([
        str(wf)[len(EX):] for wf in workflows])

    with open(path, 'w', newline='') as h:
        n_tpos, n_tneg, n_fpos, n_fneg = 0, 0, 0, 0
        w = csv.DictWriter(h, fieldnames=header)
        w.writeheader()
        for task in sorted(tasks):
            row: dict[str, str] = {"Task": task}

            expected, actual = table_expected[task], table_actual[task]

            for wf in workflows:
                s = ("●" if wf in actual else "○")
                s += ("⨯" if (wf in actual) ^ (wf in expected) else "")
                row[str(wf)[len(EX):]] = s

            n_fpos += len(actual - expected)
            n_fneg += len(expected - actual)
            n_tpos += len(actual.intersection(expected))
            n_tneg += len(workflows - expected - actual)
            w.writerow(row)
        try:
            w.writerow({
                "Precision": "{0:.3f}".format(n_tpos / (n_tpos + n_fpos)),
                "Recall": "{0:.3f}".format(n_tpos / (n_tpos + n_fneg))
            })
        except ZeroDivisionError:
            w.writerow({"Precision": "?", "Recall": "?"})


def write_evaluations(
        store: TransformationStore,
        opacities=('workflow', 'tool', 'internal'),
        passthroughs=('pass', 'block'),
        orderings=('any', 'chronological'),
        task_paths=ROOT.glob("tasks/*.ttl"),
        workflow_paths=ROOT.glob("workflows/*.ttl")) -> None:

    task_paths = list(task_paths)
    workflow_paths = list(workflow_paths)
    tools = graph(ROOT / "tools" / "tools.ttl")

    for variant in product(opacities, passthroughs, orderings):
        opacity, passthrough, ordering = variant

        if ordering == "chronological" and opacity == "workflow":
            continue

        print("Variant:", variant)

        # Build & send transformation graphs for every workflow
        for wf_path in workflow_paths:
            workflow = graph(wf_path)
            print(f"Building graph for workflow {wf_path}...")
            g = build_transformation(cct, tools, workflow,
                passthrough=(passthrough == 'pass'),
                with_intermediate_types=(opacity == 'internal'),
                with_noncanonical_types=False)
            print("Sending transformation graph to graph store...")
            store.put(g)

        # Fire query for every task
        actual: dict[str, set[Node]] = dict()
        expected: dict[str, set[Node]] = dict()
        for task_path in task_paths:
            print(f"Reading transformation graph for task {task_path}...")
            name = task_path.stem[4:]
            task_graph = graph(task_path)
            query = TransformationQuery(cct, task_graph,
                by_types=(opacity != 'workflow'),
                by_chronology=(ordering == 'chronological' and
                    opacity != 'workflow'),
                unfold_tree=True)
            expected[name] = set(task_graph.objects(query.root,
                TA.implementation))

            print("Querying graph store...")
            actual[name] = result = store.query(query)
            print(f"Results: {', '.join(str(wf) for wf in result)}")

            BUILD_DIR.mkdir(exist_ok=True)
            summary_csv(
                BUILD_DIR / f"eval-{opacity}-{passthrough}-{ordering}.csv",
                expected, actual)


if __name__ == '__main__':
    store = TransformationStore.backend(STORE_TYPE, STORE_URL,
        cred=STORE_USER)

    # Produce evaluation summaries for all variants mentioned in the paper
    write_evaluations(store)
