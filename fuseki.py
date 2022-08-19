#!/usr/bin/env python3
# Just a wrapper script that downloads and runs Apache Jena Fuseki, for easier
# testing

from __future__ import annotations

import sys
import subprocess
import requests
import tarfile
import shutil
import threading
from pathlib import Path
from typing import ContextManager

from transformation_algebra.util.common import graph, build, to_store
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
    def __init__(self, dataset: str, *args):
        self.process: (subprocess.Popen | None) = None
        self.ready = False
        self.dataset = dataset
        self.args = list(args)
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


if __name__ == '__main__':
    tools = graph(ROOT / "tools" / "tools.ttl")
    with FusekiServer("cct", *sys.argv[1:]) as server:

        # Build transformation graphs for every workflow
        for wf_path in ROOT.glob("workflows/*.ttl"):
            print(f"Building transformation graph for {wf_path}...")
            g = build(language=cct, tools=tools, workflow=graph(wf_path))
            print("Sending transformation graph to Fuseki...")
            to_store(g, backend="fuseki", url="http://localhost:3030/cct")
