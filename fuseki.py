#!/usr/bin/env python3
# Just a wrapper script that downloads and runs Apache Jena Fuseki, for easier
# testing

import sys
import subprocess
import requests
import tarfile
import shutil
from pathlib import Path
from typing import ContextManager

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
    def __init__(self, *args):
        self.process: (subprocess.Popen | None) = None
        self.args = list(args)
        self.prepare_executable()

    def __enter__(self, *args):
        assert FUSEKI_JAR.is_file()
        print(f"Running jar file at {FUSEKI_JAR}...")
        args: list[str] = [JAVA, "-Xmx4G", "-cp", str(FUSEKI_JAR),
            "org.apache.jena.fuseki.cmd.FusekiCmd"] + self.args
        self.process = subprocess.Popen(args,
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT,
            env={
                "FUSEKI_BASE": FUSEKI_DIR / "run",
                "FUSEKI_HOME": FUSEKI_DIR / FUSEKI_NAME
            }
        )
        print("Waiting for Fuseki to start...")
        for bline in self.process.stdout:
            line = bline.decode('utf-8')
            print(line, end='')
            if "INFO  Started" in line:
                break

    def __exit__(self, *args):
        print(f"Terminating Fuseki process ({self.process.pid})...")
        self.process.terminate()

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
    with FusekiServer(*sys.argv[1:]) as server:
        print("Doing something")
