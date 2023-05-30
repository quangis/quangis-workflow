#!/usr/bin/env python3
# Sends transformation graphs for all workflows to a graph store, and
# subsequently fires queries for all tasks to retrieve them back.

from __future__ import annotations

import csv
from itertools import chain, product
from pathlib import Path
from rdflib.graph import Graph
from rdflib.term import Node
from rdflib.util import guess_format

from transforge.graph import TransformationGraph
from transforge.query import TransformationQuery
from transforge.namespace import TF, shorten
from transforge.workflow import WorkflowGraph
from transforge.util.store import TransformationStore
from cct import cct

# STORE_TYPE = "fuseki"
# STORE_URL = "https://localhost:3030"
# STORE_USER = None
STORE_TYPE = "marklogic"
STORE_URL = "http://192.168.56.1:8000"
STORE_USER = ("user", "password")

ROOT = Path(__file__).parent.parent
BUILD_DIR = ROOT / "build"


def summary_csv(path: Path | str,
        table_expected: dict[str, set[Node]],
        table_actual: dict[str, set[Node]]) -> None:

    tasks = set(table_expected.keys())
    workflows = set.union(*chain(table_expected.values(),
        table_actual.values()))

    header = ["Task", "Precision", "Recall"] + sorted([
        shorten(wf) for wf in workflows])

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
                row[shorten(wf)] = s

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
        task_paths=ROOT.glob("build/task-skeletons/*.ttl"),
        workflow_paths=ROOT.glob("workflows/*.ttl")) -> None:

    task_paths = list(task_paths)
    workflow_paths = list(workflow_paths)
    tools = Graph()
    tools.parse(ROOT / "data" / "all.ttl")

    for variant in product(opacities, passthroughs, orderings):
        opacity, passthrough, ordering = variant

        if ordering == "chronological" and opacity == "workflow":
            continue

        print("Variant:", variant)

        # Build & send transformation graphs for every workflow
        for wf_path in workflow_paths:
            print(f"Building graph for workflow {wf_path}...")
            wg = WorkflowGraph(cct, tools)
            wg.parse(wf_path, format=guess_format(wf_path))
            wg.refresh()
            g = TransformationGraph(cct,
                passthrough=(passthrough == 'pass'),
                with_intermediate_types=(opacity == 'internal'),
                with_noncanonical_types=True)
            g.add_workflow(wg)
            print("Sending transformation graph to graph store...")
            store.put(g)

        # Fire query for every task
        actual: dict[str, set[Node]] = dict()
        expected: dict[str, set[Node]] = dict()
        for task_path in task_paths:
            print(f"Reading transformation graph for task {task_path}...")
            name = task_path.stem[4:]
            task_graph = Graph()
            task_graph.parse(task_path, format=guess_format(task_path))
            query = TransformationQuery(cct, task_graph,
                by_types=(opacity != 'workflow'),
                by_chronology=(ordering == 'chronological' and
                    opacity != 'workflow'),
                unfold_tree=True)
            expected[name] = set(task_graph.objects(query.root,
                TF.implementation))

            print("Querying graph store...")
            try:
                actual[name] = result = store.run(query)
            except ValueError:
                print("Warning: Some internal error")
                error = "-error"
                actual[name] = result = set()
            else:
                print(f"Results: {', '.join(str(wf) for wf in result)}")
                error = ""

        BUILD_DIR.mkdir(exist_ok=True)
        summary_csv(
            BUILD_DIR / f"eval-{opacity}-{passthrough}-{ordering}{error}.csv",
            expected, actual)



if __name__ == '__main__':
    store = TransformationStore.backend(STORE_TYPE, STORE_URL,
        cred=STORE_USER)

    # Produce evaluation summaries for all variants mentioned in the paper
    write_evaluations(store)
