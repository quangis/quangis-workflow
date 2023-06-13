"""
"""
# PASSWORD = read('password')

# from itertools import product
from pathlib import Path
# from transforge.util.utils import write_graphs
from transforge.util.store import TransformationStore

from quangis.evaluation import read_transformation, variants, \
    write_csv_summary, upload, query

ROOT = Path(__file__).parent
DATA = ROOT
TASKS = list((DATA / "tasks").glob("*.ttl"))
WORKFLOWS = list((DATA / "workflows").glob("*.ttl"))

STORE_URL = "http://192.168.56.1:8000"
STORE_USER = ("user", "password")

def task_transformation():
    """Produce transformation graphs for workflows"""

    DEST = ROOT / "build" / "transformations"
    DEST.mkdir(exist_ok=True)

    def action(wf: Path, tfm: Path) -> bool:
        tfm.parent.mkdir(exist_ok=True)
        read_transformation(wf).serialize(tfm)
        return True

    for wf in WORKFLOWS:
        tfm = DEST / "transformations" / f"{wf.stem}.ttl"
        yield dict(name=wf.stem,
            file_dep=[wf],
            targets=[tfm],
            actions=[(action, (wf, tfm))])

def task_visualize():
    """Visualizations of transformation graphs."""

    DEST = ROOT / "build" / "transformations"
    DEST.mkdir(exist_ok=True)

    def action(wf: Path, tfm: Path) -> bool:
        tfm.parent.mkdir(exist_ok=True)
        read_transformation(wf).visualize(tfm)
        return True

    for wf in WORKFLOWS:
        tfm = DEST / "transformations" / f"{wf.stem}.dot"
        yield dict(name=wf.stem,
            file_dep=[wf],
            targets=[tfm],
            actions=[(action, (wf, tfm))])

def task_evaluations():
    """Prepare queries and send evaluations."""

    DEST = ROOT / "build" / "summary"
    DEST.mkdir(exist_ok=True)

    store = TransformationStore.backend('marklogic', STORE_URL,
        cred=STORE_USER)

    def action(variant, kwargsg, kwargsq) -> bool:
        workflows = upload(WORKFLOWS, store, **kwargsg)
        expect, actual = query(TASKS, store, **kwargsq)
        with open(DEST / f"{variant}.csv") as f:
            write_csv_summary(f, expect, actual, workflows)
        return True

    for variant in variants():
        yield dict(
            name=variant[0],
            file_dep=TASKS + WORKFLOWS,
            targets=[DEST / f"{variant}.csv"],
            actions=[(action, variant)]
        )
