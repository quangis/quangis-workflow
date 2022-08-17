#!/usr/bin/env python3
# Just a wrapper script that downloads and runs Apache Jena Fuseki, for easier
# testing

import sys
import subprocess
import requests
import tarfile
from pathlib import Path

FUSEKI_DIR = Path.home() / ".fuseki"
FUSEKI_VERSION = "4.5.0"
FUSEKI_NAME = f"apache-jena-fuseki-{FUSEKI_VERSION}"
FUSEKI_URL = f"https://archive.apache.org/dist/jena/binaries/" \
    f"{FUSEKI_NAME}.tar.gz"
FUSEKI_ARCHIVE = FUSEKI_DIR / f"{FUSEKI_NAME}.tar.gz"
FUSEKI_JAR = FUSEKI_DIR / FUSEKI_NAME / "fuseki-server.jar"


if __name__ == '__main__':

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

    print(f"Running {FUSEKI_JAR}...")
    args: list[str] = ["java", "-Xmx4G", "-cp", str(FUSEKI_JAR),
        "org.apache.jena.fuseki.cmd.FusekiCmd"] + sys.argv[1:]
    subprocess.run(args,
        env={
            "FUSEKI_BASE": FUSEKI_DIR / "run",
            "FUSEKI_HOME": FUSEKI_DIR / FUSEKI_NAME
        }
    )
