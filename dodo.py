"""
"""
import sys
import functools
from itertools import chain
from pathlib import Path
# from transforge.util.utils import write_graphs
from transforge.util.store import TransformationStore
from quangis.evaluation import read_transformation, variants, \
    write_csv_summary, upload, query
from quangis.tools.repo import ToolRepository, IntegrityError

def mkdir(*paths: Path):
    for path in paths:
        try:
            if not path.exists():
                path.mkdir(parents=True)
        except AttributeError:
            pass

# TODO see https://github.com/pydoit/doit/issues/254: dependencies[i] might not 
# behave as expected


DOIT_CONFIG = {'default_tasks': [], 'continue': True}  # type: ignore

ROOT = Path(__file__).parent

# Until it gets turned into a module, this is the best I can do
QUESTION_PARSER = ROOT.parent / "geo-question-parser"
sys.path.append(str(QUESTION_PARSER))

DATA = ROOT / "data"
BUILD = ROOT / "build"
IOCONFIG = DATA / "ioconfig.ttl"
QUESTIONS = list((QUESTION_PARSER / "Data").glob("*.json"))

# Source files
TOOLS = list((DATA / "tools").glob("*.ttl"))
TASKS = list((DATA / "tasks").glob("*.ttl"))
WORKFLOWS = list((DATA / "workflows" / "expert1").glob("*.ttl"))
# These are the workflows as generated from Eric's GraphML. That process should 
# eventually be ran from here too...
CWORKFLOWS = list((DATA / "workflows" / "expert2").glob("*.ttl"))

STORE_URL = "https://qanda.soliscom.uu.nl:8000"


@functools.cache
def transformation_store() -> TransformationStore:
    print(f"Connecting to {STORE_URL}...")
    username = input("Username: ")
    password = input("Password: ")
    return TransformationStore.backend('marklogic', STORE_URL,
        cred=(username, password))


def generated_workflow_names():
    from rdflib.graph import Graph
    from rdflib.namespace import Namespace, RDF
    from rdflib.term import URIRef
    from quangis.ccd import ccd
    from quangis.polytype import Polytype
    from quangis.namespace import CCD

    # Find sources and goals from configuration
    confgraph = Graph()
    confgraph.parse(IOCONFIG)
    base = Namespace(IOCONFIG.parent.absolute().as_uri() + "/")

    sources = [
        list(y for y in confgraph.objects(x, RDF.type)
            if isinstance(y, URIRef))
        for x in confgraph.objects(None, base.input)]

    goals = [
        list(y for y in confgraph.objects(x, RDF.type)
            if isinstance(y, URIRef))
        for x in confgraph.objects(None, base.output)]

    # To start with, we generate workflows with two inputs and one output, 
    # of which one input is drawn from the following sources, and the other 
    # is the same as the output without the measurement level.
    inputs_outputs = []
    for goal_tuple in goals:
        goal = Polytype.project(ccd.dimensions, goal_tuple)
        source1 = Polytype(ccd.dimensions, goal)
        source1[CCD.NominalA] = {CCD.NominalA}
        for source_tuple in sources:
            source2 = Polytype.project(ccd.dimensions, source_tuple)
            inputs_outputs.append(([source1, source2], [goal]))

    # Finally add names
    for inputs, outputs in inputs_outputs:
        namei = "-".join(sorted(i.canonical_name() for i in inputs))
        nameo = "-".join(sorted(o.canonical_name() for o in outputs))
        name = f"{namei}--{nameo}"
        yield name, inputs, outputs


GENERATED_WORKFLOWS_INCL = list(generated_workflow_names())
GEN_WORKFLOWS = [BUILD / "workflows" / "gen" / f"{wf[0]}.ttl"
    for wf in GENERATED_WORKFLOWS_INCL]

ALL_WORKFLOWS = []
ALL_WORKFLOWS += WORKFLOWS
ALL_WORKFLOWS += [BUILD / "workflows" / "expert2" / f"{wf.stem}.ttl"
    for wf in CWORKFLOWS]
ALL_WORKFLOWS += GEN_WORKFLOWS

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

def task_tfm():
    """Produce all transformation graphs for workflows."""

    def action(dependencies, targets) -> bool:
        from rdflib import Graph
        # Quick workaround for https://github.com/pydoit/doit/issues/254
        wf = next(x for x in dependencies if not x.endswith("abstract.ttl"))
        tfm = targets[0]
        tools = Graph()
        tools.parse(BUILD / "tools" / "abstract.ttl")
        read_transformation(wf, tools).serialize(tfm)
        return True

    dest = BUILD / "transformations"
    for path in ALL_WORKFLOWS:
        destdir = dest / f"{path.parent.stem}"
        yield dict(name=path.stem,
            file_dep=[path, BUILD / "tools" / "abstract.ttl"],
            targets=[destdir / f"{path.stem}.ttl"],
            actions=[(mkdir, [destdir]), action])

def task_tfm_expert1():
    return dict(task_dep=[f"tfm:{x.stem}" for x in WORKFLOWS],
        actions=None)

def task_tfm_expert2():
    return dict(task_dep=[f"tfm:{x.stem}" for x in CWORKFLOWS],
        actions=None)

def task_tfm_gen():
    return dict(task_dep=[f"tfm:{x.stem}" for x in GEN_WORKFLOWS],
        actions=None)

def task_ml_upload():
    """Send known transformation graphs to MarkLogic."""

    # No dependencies because we just want to send any transformation graph 
    # that is generated; not force generation first
    def action(dependencies):
        from quangis.cct import cct
        from quangis.namespace import RDF, WF
        from rdflib import URIRef
        from transforge.graph import TransformationGraph
        store = transformation_store()

        files = [
            BUILD / "transformations" / f"{x.parent.stem}" / f"{x.stem}.ttl"
            for x in chain(WORKFLOWS, CWORKFLOWS, GEN_WORKFLOWS)]

        for d in files:
            sys.stderr.write(f"Uploading {d}...\n")
            if not d.exists():
                continue
            g = TransformationGraph(cct)
            g.parse(d)
            root = g.value(None, RDF.type, WF.Workflow, any=False)
            if root:
                assert isinstance(root, URIRef)
                g.uri = root
                result = store.put(g)
                sys.stderr.write(f"Uploaded with {str(result)}...\n")

    return dict(
        file_dep=[],
        actions=[action],
        uptodate=[False],
        verbosity=2
    )

def task_viz_dot():
    """Visualizations of transformation graphs."""

    def action(dependencies, targets) -> bool:
        from quangis.cct import cct
        from transforge.graph import TransformationGraph
        g = TransformationGraph(cct)
        g.parse(dependencies[0])
        g.visualize(targets[0])
        return True

    for path in ALL_WORKFLOWS:
        srcdir = BUILD / "transformations" / f"{path.parent.stem}"
        destdir = BUILD / "visualizations" / f"{path.parent.stem}"
        yield dict(name=path.stem,
            file_dep=[srcdir / f"{path.stem}.ttl"],
            targets=[destdir / f"{path.stem}.dot"],
            actions=[(mkdir, [destdir]), action])

def task_viz_pdf():
    """Visualizations of transformation graphs as a PDF."""

    def action(dependencies, targets) -> bool:
        import pydot  # type: ignore
        graphs = pydot.graph_from_dot_file(dependencies[0])
        graphs[0].write_pdf(targets[0])
        return True

    destdir = BUILD / "transformations"

    for path in ALL_WORKFLOWS:
        destdir = BUILD / "visualizations" / f"{path.parent.stem}"
        yield dict(name=path.stem,
            file_dep=[destdir / f"{path.stem}.dot"],
            targets=[destdir / f"{path.stem}.pdf"],
            actions=[(mkdir, [destdir]), action])

def task_viz_pdf_expert1():
    return dict(task_dep=[f"viz_pdf:{x.stem}" for x in WORKFLOWS],
        actions=None)

def task_viz_pdf_expert2():
    return dict(task_dep=[f"viz_pdf:{x.stem}" for x in CWORKFLOWS],
        actions=None)

def task_viz_pdf_gen():
    return dict(task_dep=[f"viz_pdf:{x.stem}" for x in GEN_WORKFLOWS],
        actions=None)

def task_ml_query_expert1():
    """Evaluate expert1 workflows' transformations against tasks.
    For this, graphs are sent to the triple store and then queried."""

    destdir = BUILD / "eval_tasks"

    def action(variant, kwargsg, kwargsq) -> bool:
        store = transformation_store()
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

def task_wf_expert2():
    """Produce abstract workflows from concrete workflows."""

    destdir = BUILD / "workflows" / "expert2"
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


def task_wf_gen_raw():
    """Synthesize new abstract workflows using APE."""

    destdir = BUILD / "workflows" / "gen-raw"
    apedir = BUILD / "ape"

    @functools.cache
    def generator():
        from quangis.synthesis import WorkflowGenerator
        gen = WorkflowGenerator(BUILD / "tools" / "abstract.ttl",
            BUILD / "tools" / "multi.ttl",
            DATA / "tools" / "arcgis.ttl", build_dir=apedir)
        return gen

    def action(name, target, inputs, outputs) -> bool:
        from rdflib import Graph
        from quangis.namespace import WFGEN, bind_all

        gen = generator()
        solutions_raw = Graph()
        for wf in gen.run(inputs, outputs, solutions=1, prefix=WFGEN[name]):
            solutions_raw += wf
        bind_all(solutions_raw)
        solutions_raw.serialize(target, format="ttl")
        return True

    for name, inputs, outputs in GENERATED_WORKFLOWS_INCL:
        target = destdir / f"{name}.ttl"
        yield dict(
            name=name,
            file_dep=[BUILD / "tools" / "abstract.ttl",
                BUILD / "tools" / "multi.ttl",
                DATA / "tools" / "arcgis.ttl"],
            targets=[target],
            actions=[(mkdir, [destdir, apedir]),
                (action, [name, target, inputs, outputs])])

def task_wf_gen():
    """Hack around limitations of APE; see issue #18."""

    @functools.cache
    def tool_repo():
        return ToolRepository.from_file(BUILD / "tools" / "abstract.ttl", 
            check_integrity=True)

    def action(dependencies, targets) -> bool:
        from rdflib import Graph
        from quangis.namespace import RDF, WF, bind_all
        repo = tool_repo()
        orig = Graph()
        orig.parse(dependencies[0])
        if (None, RDF.type, WF.Workflow) in orig:
            solution = repo.input_permutation_hack(orig)
        else:
            solution = orig
        bind_all(solution)
        solution.serialize(targets[0], format="ttl")
        return True

    for dest in GEN_WORKFLOWS:
        name = dest.stem
        src = BUILD / "workflows" / "gen-raw" / f"{name}.ttl"
        yield dict(name=name,
            file_dep=[src],
            targets=[dest],
            actions=[(mkdir, [dest.parent]), action])

def task_question_parse():
    """Parse question blocks JSON into JSON with bells and whistles."""

    def action(dependencies, targets) -> bool:
        import json
        from QuestionParser import QuestionParser  # type: ignore
        from TypesToQueryConverter import TQConverter  # type: ignore

        with open(dependencies[0], 'r') as f:
            input = json.load(f)

        output = []
        for question_block in input:
            parser = QuestionParser()
            qParsed = parser.parseQuestionBlock(question_block)
            cctAnnotator = TQConverter()
            cctAnnotator.cctToQuery(qParsed, True, True)
            cctAnnotator.cctToExpandedQuery(qParsed, False, False)
            output.append(qParsed)

        with open(targets[0], 'w') as f:
            json.dump(output, f, indent=4)

        return True

    for qb in QUESTIONS:
        dest = BUILD / "query" / f"{qb.stem}.json"
        yield dict(
            name=qb.stem,
            file_dep=[qb],
            targets=[dest],
            actions=[(mkdir, [dest.parent]), action]
        )

def task_question_transformation():
    """Convert parsed questions into task transformation graphs, including 
    SPARQL queries."""

    def action(dependencies, targets) -> bool:
        import json
        from rdflib.term import BNode, Literal
        from transforge.namespace import TF, RDF, RDFS
        from transforge.graph import TransformationGraph
        from transforge.query import transformation2sparql
        from transforge.type import Product, TypeOperation
        from quangis.cct import cct, R3, R2, Obj, Reg

        with open(dependencies[0], 'r') as f:
            inputs = json.load(f)

        g = TransformationGraph(cct)
        for parsed_question in inputs:
            task = BNode()
            g.add((task, RDF.type, TF.Task))
            g.add((task, RDFS.comment, Literal(parsed_question['question'])))

            def dict2graph(q: dict) -> BNode:
                node = BNode()
                t = cct.parse_type(q['after']['cct']).concretize(replace=True)

                # This is a temporary solution: R(x * z, y) is for now
                # converted to the old-style R3(x, y, z)
                if isinstance(t.params[0], TypeOperation) and \
                        t.params[0].operator == Product:
                    t = R3(t.params[0].params[0], t.params[1], t.params[0].params[1])

                # Another temporary solution. the question parser often returns `R(Obj,
                # x)` where the manually constructed queries ("gold standard") would
                # use `R(Obj, Reg * x)`. So, whenever we encounter the former, we will
                # manually also allow the latter, cf.
                # <https://github.com/quangis/transformation-algebra/issues/79#issuecomment-1210661153>
                if isinstance(t.params[0], TypeOperation) and \
                        t.operator == R2 and \
                        t.params[0].operator == Obj and \
                        t.params[1].operator != Product:
                    g.add((node, TF.type, cct.uri(R2(t.params[0], Reg * t.params[1]))))

                g.add((node, TF.type, cct.uri(t)))
                for b in q.get('before', ()):
                    g.add((node, TF['from'], dict2graph(b)))

                return node

            g.add((task, TF.output, dict2graph(parsed_question['queryEx'])))

        for taskroot in g.subjects(RDF.type, TF.Task):
            q = transformation2sparql(g, root=taskroot)
            g.add((taskroot, TF.sparql, Literal(q)))

        g.serialize(targets[0])
        return True

    for qb in QUESTIONS:
        src = BUILD / "query" / f"{qb.stem}.json"
        dest = BUILD / "query" / f"{qb.stem}.ttl"
        yield dict(
            name=qb.stem,
            file_dep=[src],
            targets=[dest],
            actions=[(mkdir, [dest.parent]), action]
        )

def task_ml_query_questions():
    """Send queries to MarkLogic."""

    def action(dependencies, targets):
        from rdflib import Graph, Literal
        from transforge.namespace import TF

        store = transformation_store()
        g = Graph()
        g.parse(dependencies[0])
        for task, sparql in g.subject_objects(TF.sparql):
            try:
                matches = [r.workflow for r in store.store.query(sparql.value)]
            except Exception as e:
                matches = [Literal(f"{type(e)}: {e}")]
            for m in matches:
                g.add((task, TF.match, m))

    for qb in QUESTIONS:
        src = BUILD / "query" / f"{qb.stem}.ttl"
        dest = BUILD / "query" / f"{qb.stem}.results.ttl"
        yield dict(
            name=qb.stem,
            file_dep=[src],
            targets=[dest],
            actions=[(mkdir, [dest.parent]), action],
            verbosity=2
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

    return dict(actions=[action], verbosity=2)

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

