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
TOOLS = DATA / "data" / "all.ttl"
TASKS = list((DATA / "tasks").glob("*.ttl"))
WORKFLOWS = list((DATA / "workflows").glob("*.ttl"))

# These are the workflows as generated from Eric's GraphML. That process should 
# eventually be ran from here too...
CWORKFLOWS = list((DATA / "workflows-concrete").glob("*.ttl"))

STORE_URL = "http://192.168.56.1:8000"
STORE_USER = ("user", "password")

def task_cct():
    """Produce CCT vocabulary file."""
    DEST = ROOT / "build" / "cct.ttl"

    def action():
        from cct import cct
        from transforge.graph import TransformationGraph
        g = TransformationGraph(cct)
        g.add_vocabulary()
        g.serialize(DEST)

    return dict(
        file_dep=[ROOT / "quangis" / "cctrans.py"],
        targets=[DEST],
        actions=[action]
    )

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


def task_update_tools():
    """Extract a tool repository from concrete workflows."""

    DEST = ROOT / "build" / "repo.ttl"

    def action() -> bool:
        from quangis.tools.repo import Repo
        from quangis.workflow import Workflow
        repo = Repo.from_file(TOOLS, check_integrity=True)
        for wf_path in CWORKFLOWS:
            cwf = Workflow.from_file(wf_path)
            repo.update(cwf)
        graph = repo.graph()
        graph.serialize(DEST)
        return True

    return dict(
        file_dep=CWORKFLOWS,
        targets=[DEST],
        actions=[action]
    )

def task_abstract():
    """Produce abstract workflows from concrete workflows."""

    DEST = ROOT / "build" / "abstract"
    repo_path = ROOT / "build" / "repo.ttl"

    def action(wf_path, target):
        from quangis.workflow import Workflow
        from quangis.tools.repo import Repo
        DEST.mkdir(exist_ok=True)

        # Todo: this should be produced by an action itself
        repo = Repo.from_file(repo_path, check_integrity=False)

        cwf = Workflow.from_file(wf_path)
        print(cwf.serialize())

        g = repo.convert_to_abstractions(cwf, cwf.root)
        g.serialize(target, format="ttl")

    for wf in CWORKFLOWS:
        yield dict(
            name=wf.name,
            file_dep=[wf],
            targets=[DEST / wf.name],
            actions=[(action, [wf, DEST / wf.name])]
        )
