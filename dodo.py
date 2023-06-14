"""
"""
# PASSWORD = read('password')

# from itertools import product
from pathlib import Path
# from transforge.util.utils import write_graphs
from transforge.util.store import TransformationStore
from quangis.evaluation import read_transformation, variants, \
    write_csv_summary, upload, query

DOIT_CONFIG = {'default_tasks': []}  # type: ignore

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IOCONFIG = DATA / "ioconfig.ttl"
TOOLS = DATA / "all.ttl"
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

def task_transformations_ttl():
    """Produce transformation graphs for workflows."""

    DEST = ROOT / "build" / "transformations"
    DEST.mkdir(exist_ok=True)

    def action(wf: Path, tfm: Path) -> bool:
        read_transformation(wf).serialize(tfm)
        return True

    for wf in WORKFLOWS:
        tfm = DEST / "transformations" / f"{wf.stem}.ttl"
        yield dict(name=wf.stem,
            file_dep=[wf],
            targets=[tfm],
            actions=[(action, (wf, tfm))])

def task_transformations_visual():
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


def task_evaluate():
    """Prepare queries and send evaluations."""

    DEST = ROOT / "build" / "eval"

    store = TransformationStore.backend('marklogic', STORE_URL,
        cred=STORE_USER)

    def action(variant, kwargsg, kwargsq) -> bool:
        DEST.mkdir(exist_ok=True)
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

def task_generate():
    """Synthesize workflows using APE."""

    DESTDIR = ROOT / "build" / "generated"

    def action() -> bool:
        from rdflib.graph import Graph
        from rdflib.namespace import Namespace, RDF
        from rdflib.term import URIRef
        from quangis.polytype import Polytype
        from quangis.synthesis import WorkflowGenerator
        from quangis.namespace import CCD, EX
        from quangis.ccdata import dimensions

        confgraph = Graph()
        confgraph.parse(IOCONFIG)
        base = Namespace(IOCONFIG.parent.absolute().as_uri() + "/")
        sources: list[list[URIRef]] = [
            list(y for y in confgraph.objects(x, RDF.type)
                 if isinstance(y, URIRef))
            for x in confgraph.objects(None, base.input)]
        goals: list[list[URIRef]] = [
            list(y for y in confgraph.objects(x, RDF.type)
                 if isinstance(y, URIRef))
            for x in confgraph.objects(None, base.output)]

        DESTDIR.mkdir(exist_ok=True)
        gen = WorkflowGenerator(TOOLS, DESTDIR)

        inputs_outputs: list[tuple[list[Polytype], list[Polytype]]] = []

        # To start with, we generate workflows with two inputs and one output, 
        # of which one input is drawn from the following sources, and the other 
        # is the same as the output without the measurement level.
        for goal_tuple in goals:
            goal = Polytype.project(dimensions, goal_tuple)
            source1 = Polytype(goal)
            source1[CCD.NominalA] = {CCD.NominalA}
            for source_tuple in sources:
                source2 = Polytype.project(dimensions, source_tuple)
                inputs_outputs.append(([source1, source2], [goal]))

        running_total = 0
        for run, (inputs, outputs) in enumerate(inputs_outputs):
            print(f"Attempting [ {' ] & [ '.join(x.short() for x in inputs)} "
                f"] -> [ {' & '.join(x.short() for x in outputs)} ]")
            for solution in gen.run(inputs, outputs, solutions=1, 
                    prefix=EX.solution):
                running_total += 1
                path = DESTDIR / f"solution{running_total}.ttl"
                print(f"Writing solution: {path}")
                solution.serialize(path, format="ttl")
            print(f"Running total is {running_total}.")

        return True

    return dict(
        file_dep=[IOCONFIG, TOOLS],
        targets=[DESTDIR / "solution1.ttl"],
        actions=[(action, [])],
    )
