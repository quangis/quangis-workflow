#!/usr/bin/env python3
# Just a wrapper script that downloads and runs Apache Jena Fuseki, for easier
# testing

from __future__ import annotations

import sys
import csv
import subprocess
import requests
import tarfile
import shutil
import threading
from itertools import chain
from pathlib import Path
from rdflib.term import Node
from typing import ContextManager

from transformation_algebra import TransformationQuery
from transformation_algebra.namespace import TA, REPO
from transformation_algebra.util.store import TransformationStore
from transformation_algebra.util.common import (graph, build_transformation)
from cct.language import cct

ROOT = Path(__file__).parent
JAVA = shutil.which("java")
FUSEKI_DIR = ROOT / "fuseki"
FUSEKI_VERSION = "4.5.0"
FUSEKI_NAME = f"apache-jena-fuseki-{FUSEKI_VERSION}"
FUSEKI_URL = f"https://archive.apache.org/dist/jena/binaries/" \
    f"{FUSEKI_NAME}.tar.gz"
FUSEKI_ARCHIVE = FUSEKI_DIR / f"{FUSEKI_NAME}.tar.gz"
FUSEKI_JAR = FUSEKI_DIR / FUSEKI_NAME / "fuseki-server.jar"


class FusekiServer(ContextManager):
    def __init__(self, dataset: str = "test_dataset"):
        self.process: (subprocess.Popen | None) = None
        self.url = f"http://localhost:3030/{dataset}"
        self.ready = False
        self.dataset = dataset
        self.prepare_executable()

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        print(f"Terminating Fuseki process ({self.process.pid})...")
        self.process.terminate()

    def run(self):
        assert FUSEKI_JAR.is_file() and not self.process
        print(f"Running jar file at {FUSEKI_JAR}...")

        def run_fuseki_process():
            args: list[str] = [JAVA, "-Xmx4G", "-cp", str(FUSEKI_JAR),
                "org.apache.jena.fuseki.cmd.FusekiCmd",
                "--localhost", "--mem", f"/{self.dataset}"]
            self.process = subprocess.Popen(args,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={
                    "FUSEKI_BASE": FUSEKI_DIR / "run",
                    "FUSEKI_HOME": FUSEKI_DIR / FUSEKI_NAME
                }
            )
            print("Waiting for Fuseki to start...")
            for line in self.process.stdout:
                print(line, end='')
                if not self.ready and "INFO  Started" in line:
                    self.ready = True

        t1 = threading.Thread(target=run_fuseki_process)
        t1.start()
        while not self.ready:
            pass

    def prepare_executable(self):
        """
        Download JAR file for Fuseki if it isn't already present.
        """
        if not FUSEKI_JAR.is_file():
            if not FUSEKI_DIR.is_dir():
                FUSEKI_DIR.mkdir(parents=True)

            if not FUSEKI_ARCHIVE.is_file():
                print(f"Downloading from {FUSEKI_URL}...")
                r = requests.get(FUSEKI_URL)
                print(f"Writing to {FUSEKI_ARCHIVE}...")
                with open(FUSEKI_ARCHIVE, 'wb') as f:
                    f.write(r.content)
                assert FUSEKI_ARCHIVE.is_file()

            print(f"Unpacking {FUSEKI_ARCHIVE}...")
            tar = tarfile.open(name=FUSEKI_ARCHIVE, mode='r:*')
            tar.extractall(path=FUSEKI_DIR)
        assert FUSEKI_JAR.is_file()


def summary_csv(path: Path | str,
        table_expected: dict[str, set[Node]],
        table_actual: dict[str, set[Node]]) -> None:

    tasks = set(table_expected.keys())
    workflows = set.union(*chain(table_expected.values(),
        table_actual.values()))

    header = ["Task", "Precision", "Recall"] + sorted([
        str(wf)[len(REPO):] for wf in workflows])

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
                row[str(wf)[len(REPO):]] = s

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


if __name__ == '__main__':
    tools = graph(ROOT / "tools" / "tools.ttl")

    with FusekiServer() as server:

        # Connect to Fuseki as client
        store = TransformationStore.backend("fuseki", server.url)

        # Build & send transformation graphs for every workflow
        for wf_path in ROOT.glob("workflows/*.ttl"):
            workflow = graph(wf_path)
            print(f"Building transformation graph for workflow {wf_path}...")
            g = build_transformation(cct, tools, workflow)
            # print(g.serialize(format="ttl"))
            print("Sending transformation graph to Fuseki...")
            store.put(g)

        # Build & fire query for every task
        actual: dict[str, set[Node]] = dict()
        expected: dict[str, set[Node]] = dict()
        for task_path in ROOT.glob("tasks/*.ttl"):
            print(f"Reading transformation graph for task {task_path}...")
            name = task_path.stem
            task_graph = graph(task_path)
            query = TransformationQuery(cct, task_graph,
                by_io=False,
                by_types=False,
                by_chronology=False,
                unfold_tree=False)
            expected[name] = set(task_graph.objects(query.root,
                TA.implementation))

            print("Querying Fuseki...")
            actual[name] = result = store.query(query)
            print(result)

            # print(f"Results: {', '.join(str(wf) for wf in actual[name])}")

        summary_csv("summary.csv", expected, actual)
