"""
"""
# PASSWORD = read('password')

# from itertools import product
from pathlib import Path
# from transforge.util.utils import write_graphs
from transforge.util.store import TransformationStore
from quangis.evaluation import read_transformation, variants, \
    write_csv_summary, upload, query
from quangis.tools.repo import ToolRepository, IntegrityError

def mkdir(*paths: Path):
    for path in paths:
        path.mkdir(exist_ok=True, parents=True)

# TODO see https://github.com/pydoit/doit/issues/254: dependencies[i] might not 
# behave as expected


DOIT_CONFIG = {'default_tasks': [], 'continue': True}  # type: ignore

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IOCONFIG = DATA / "ioconfig.ttl"

# Source files
TOOLS = list((DATA / "tools").glob("*.ttl"))
TASKS = list((DATA / "tasks").glob("*.ttl"))
WORKFLOWS = list((DATA / "workflows").glob("*.ttl"))

# Created files
BUILD = ROOT / "build"
BWORKFLOWS = BUILD / "workflows"
BTRANSFORMATIONS = BUILD / "transformations"
BTOOLS = BUILD / "tools"
BQUERIES = BUILD / "queries"

# These are the workflows as generated from Eric's GraphML. That process should 
# eventually be ran from here too...
CWORKFLOWS = list((DATA / "workflows-concrete").glob("*.ttl"))

STORE_URL = "http://192.168.56.1:8000"
STORE_USER = ("user", "password")

def task_vocab_cct():
    """Produce CCT vocabulary file."""

    def action(targets):
        from cct import cct
        from transforge.graph import TransformationGraph
        g = TransformationGraph(cct)
        g.add_vocabulary()
        g.serialize(targets[0])

    return dict(
        file_dep=[ROOT / "quangis" / "cct.py"],
        targets=[BUILD / "cct.ttl"],
        actions=[(mkdir, [BUILD]), action]
    )

def task_transformations():
    """Produce transformation graphs for workflows."""

    def action(dependencies, targets) -> bool:
        wf, tfm = dependencies[0], targets[0]
        read_transformation(wf).serialize(tfm)
        return True

    destdir = BUILD / "transformations"
    for wf in WORKFLOWS:
        yield dict(name=wf.stem,
            file_dep=[wf],
            targets=[destdir / f"{wf.stem}.ttl"],
            actions=[(mkdir, [destdir]), action])

def task_transformations_dot():
    """Visualizations of transformation graphs."""

    def action(dependencies, targets) -> bool:
        from quangis.cct import cct
        from transforge.graph import TransformationGraph
        g = TransformationGraph(cct)
        g.parse(dependencies[0])
        g.visualize(targets[0])
        return True

    destdir = BUILD / "transformations"
    for wf in WORKFLOWS:
        yield dict(name=wf.stem,
            file_dep=[destdir / f"{wf.stem}.ttl"],
            targets=[destdir / f"{wf.stem}.dot"],
            actions=[(mkdir, [destdir]), action])

def task_transformations_pdf():
    """Visualizations of transformation graphs as a PDF."""

    def action(dependencies, targets) -> bool:
        import pydot  # type: ignore
        graphs = pydot.graph_from_dot_file(dependencies[0])
        graphs[0].write_pdf(targets[0])
        return True

    destdir = BUILD / "transformations"

    for wf in WORKFLOWS:
        yield dict(name=wf.stem,
            file_dep=[destdir / f"{wf.stem}.dot"],
            targets=[destdir / f"{wf.stem}.pdf"],
            actions=[(mkdir, [destdir]), action])

def task_eval_tasks():
    """Evaluate workflows' transformations against tasks.
    For this, graphs are sent to the triple store and then queried."""

    destdir = BUILD / "eval_tasks"

    store = TransformationStore.backend('marklogic', STORE_URL,
        cred=STORE_USER)

    def action(variant, kwargsg, kwargsq) -> bool:
        workflows = upload(WORKFLOWS, store, **kwargsg)
        expect, actual = query(TASKS, store, **kwargsq)
        with open(destdir / f"{variant}.csv") as f:
            write_csv_summary(f, expect, actual, workflows)
        return True

    for variant in variants():
        yield dict(
            name=variant[0],
            file_dep=TASKS + WORKFLOWS,
            targets=[destdir / f"{variant}.csv"],
            actions=[(mkdir, [destdir]), (action, variant)]
        )


def task_tool_repo_update():
    """Extract a tool repository from concrete workflows."""

    destdir = BUILD / "tools"

    def action() -> bool:
        from rdflib import Graph
        from quangis.namespace import TOOL, bind_all
        from quangis.tools.repo import ToolRepository
        from quangis.workflow import Workflow
        repo = ToolRepository.from_file(*TOOLS, check_integrity=True)
        for wf_path in CWORKFLOWS:
            cwf = Workflow.from_file(wf_path)
            repo.update(cwf)

        composites = Graph()
        for multi in repo.composites.values():
            multi.to_graph(composites)
        bind_all(composites, default=TOOL)
        abstractions = Graph()
        for abstr in repo.abstractions.values():
            abstr.to_graph(abstractions)
        bind_all(abstractions, default=TOOL)
        composites.serialize(destdir / "multi.ttl")
        abstractions.serialize(destdir / "abstract.ttl")
        return True

    return dict(
        file_dep=CWORKFLOWS + TOOLS,
        targets=[destdir / "multi.ttl", destdir / "abstract.ttl"],
        actions=[(mkdir, [destdir]), action]
    )

def task_wf_abstract():
    """Produce abstract workflows from concrete workflows."""

    destdir = BUILD / "abstract"
    tools = [
        BUILD / "tools" / "abstract.ttl",
        BUILD / "tools" / "multi.ttl",
        DATA / "tools" / "arcgis.ttl"]

    def action(wf_path, target):
        from quangis.workflow import Workflow
        from quangis.tools.repo import ToolRepository

        # TODO: this should be produced by an action itself
        repo = ToolRepository.from_file(*tools, check_integrity=False)

        cwf = Workflow.from_file(wf_path)
        print(cwf.serialize())

        g = repo.convert_to_abstractions(cwf, cwf.root)
        g.serialize(target, format="ttl")

    for wf in CWORKFLOWS:
        yield dict(
            name=wf.name,
            file_dep=[wf] + tools,
            targets=[destdir / wf.name],
            actions=[
                (mkdir, [destdir]),
                (action, [wf, destdir / wf.name])]
        )

def task_wf_generate():
    """Synthesize new abstract workflows using APE."""

    destdir = BUILD / "workflows" / "gen"
    apedir = BUILD / "ape"

    def action(dependencies) -> bool:
        from rdflib.graph import Graph
        from rdflib.namespace import Namespace, RDF
        from rdflib.term import URIRef
        from quangis.polytype import Polytype
        from quangis.synthesis import WorkflowGenerator
        from quangis.namespace import CCD, EX, WFGEN
        from quangis.ccd import ccd

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

        gen = WorkflowGenerator(BUILD / "tools" / "abstract.ttl",
            BUILD / "tools" / "multi.ttl",
            DATA / "tools" / "arcgis.ttl", build_dir=apedir)

        inputs_outputs: list[tuple[list[Polytype], list[Polytype]]] = []

        # To start with, we generate workflows with two inputs and one output, 
        # of which one input is drawn from the following sources, and the other 
        # is the same as the output without the measurement level.
        for goal_tuple in goals:
            goal = Polytype.project(ccd.dimensions, goal_tuple)
            source1 = Polytype(ccd.dimensions, goal)
            source1[CCD.NominalA] = {CCD.NominalA}
            for source_tuple in sources:
                source2 = Polytype.project(ccd.dimensions, source_tuple)
                inputs_outputs.append(([source1, source2], [goal]))

        running_total = 0
        for run, (inputs, outputs) in enumerate(inputs_outputs):

            namei = "-".join(sorted(i.canonical_name() for i in inputs))
            nameo = "-".join(sorted(o.canonical_name() for o in outputs))
            name = f"{namei}--{nameo}"

            for solution in gen.run(inputs, outputs, solutions=1, 
                    prefix=WFGEN[name]):
                solution.serialize(destdir / f"{name}.ttl", format="ttl")
            print(f"Running total is {running_total}.")

        return True

    return dict(
        file_dep=[IOCONFIG,
            BUILD / "tools" / "abstract.ttl",
            BUILD / "tools" / "multi.ttl",
            DATA / "tools" / "arcgis.ttl"],
        targets=[destdir / "solution1.ttl"],
        actions=[(mkdir, [destdir, apedir]), action],
    )

def task_test():
    """Run all tests."""
    return dict(
        actions=None,
        task_dep=['test_unittest', 'test_tool_repo'],
        verbosity=2
    )

def task_test_unittest():
    """Perform unit tests for checking the code."""
    def action():
        import pytest
        pytest.main(list((ROOT / "tests").glob("test_*.py")))

    return dict(
        actions=[action],
        verbosity=2
    )

def task_test_tool_repo():
    """Check integrity of tool file."""
    def action(method) -> bool:
        repo = ToolRepository.from_file(*TOOLS, check_integrity=False)
        try:
            method(repo)
        except IntegrityError:
            raise
        else:
            return True

    for attr in dir(ToolRepository):
        if attr.startswith("check_") and not attr == "check_integrity":
            yield dict(
                name=attr,
                actions=[(action, [getattr(ToolRepository, attr)])],
                verbosity=2
            )
