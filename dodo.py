"""To the next person: sorry about the state of this repository."""
import sys
import functools
from itertools import chain
from pathlib import Path
# from transforge.util.utils import write_graphs
from transforge.util.store import TransformationStore
from quangis.evaluation import read_transformation, variants, \
    write_csv_summary, upload, query
from quangis.tools.set import ToolSet, IntegrityError

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
QUESTIONS = list((QUESTION_PARSER / "Data").glob("*retri.json"))

# Source files
TOOLS = list((DATA / "tools").glob("*.ttl"))
TASKS = list((DATA / "tasks").glob("*.ttl"))
WORKFLOWS = list((DATA / "workflows" / "expert1").glob("*.ttl"))
# These are the workflows as generated from Eric's GraphML. That process should 
# eventually be ran from here too...
CWORKFLOWS = list((DATA / "workflows" / "expert2").glob("*.ttl"))
VOCAB = BUILD / "cct.ttl"

# STORE_URL = "https://qanda.soliscom.uu.nl:8000"
# STORE_URL = "http://uu080967.soliscom.uu.nl:8000"

# When running on WSL2, figure out IP of Windows host with ipconfig
# STORE_URL = "http://192.168.2.3:8000"
STORE_URL = "http://localhost:3030/cct"
STORE_TYPE = "fuseki"


@functools.cache
def transformation_store() -> TransformationStore:
    print(f"Connecting to {STORE_URL}...")
    if STORE_TYPE == "marklogic":
        username = input("Username: ")
        password = input("Password: ")
        return TransformationStore.backend('marklogic', STORE_URL,
            cred=(username, password))
    else:
        return TransformationStore.backend('fuseki', STORE_URL)


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
        g = TransformationGraph(cct, with_canonical_types=True)
        g.add_vocabulary()
        g.serialize(targets[0])

    return dict(
        file_dep=[ROOT / "quangis" / "cct.py"],
        targets=[VOCAB],
        actions=[(mkdir, [VOCAB.parent]), action]
    )

def task_tfm():
    """Produce all transformation graphs for existing workflows."""

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

def task_ml_upload_cct():
    """Upload CCT types to MarkLogic."""
    def action(dependencies):
        from quangis.cct import cct, CCT
        from rdflib import URIRef
        from transforge.graph import TransformationGraph
        store = transformation_store()
        g = TransformationGraph(cct)
        g.parse(VOCAB)
        store.put(g, URIRef(str(CCT).strip("#/")))

    return dict(
        file_dep=[VOCAB],
        actions=[action],
        uptodate=[False],
        verbosity=2
    )


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

        files = list((BUILD / "transformations").glob("**/*.ttl"))

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
        task_dep=["ml_upload_cct"],
        file_dep=[],
        actions=[action],
        uptodate=[False],
        verbosity=2
    )

def task_viz_dot():
    """Visualizations of existing transformation graphs."""

    def action(dependencies, targets) -> bool:
        from quangis.cct import cct
        from transforge.graph import TransformationGraph
        g = TransformationGraph(cct)
        g.parse(dependencies[0])
        g.visualize(targets[0])
        return True

    for path in (BUILD / "transformations").glob("**/*.ttl"):
        destdir = BUILD / "visualizations"
        yield dict(name=path.stem,
            file_dep=[path],
            targets=[destdir / f"{path.stem}.dot"],
            actions=[(mkdir, [destdir]), action])

def task_viz_pdf():
    """Visualizations of existing transformation graphs as PDF."""

    def action(dependencies, targets) -> bool:
        import pydot  # type: ignore
        graphs = pydot.graph_from_dot_file(dependencies[0])
        graphs[0].write_pdf(targets[0])
        return True

    destdir = BUILD / "transformations"

    for path in (BUILD / "transformations").glob("**/*.ttl"):
        destdir = BUILD / "visualizations"
        yield dict(name=path.stem,
            file_dep=[destdir / f"{path.stem}.dot"],
            targets=[destdir / f"{path.stem}.pdf"],
            actions=[(mkdir, [destdir]), action])

def task_ml_query_expert1():
    """Evaluate expert1 workflows' transformations against tasks.
    For this, graphs are sent to the triple store and then queried."""

    destdir = BUILD / "eval_tasks"

    def action(variant, kwargsg, kwargsq) -> bool:
        from rdflib import Graph
        store = transformation_store()

        tools = Graph()
        tools.parse(BUILD / "tools" / "abstract.ttl")

        workflows = upload(WORKFLOWS, tools, store, **kwargsg)
        with open(destdir / f"{variant}.txt", 'w') as f:
            expect, actual = query(TASKS, store, log=f, **kwargsq)
        with open(destdir / f"{variant}.csv", 'w') as f:
            write_csv_summary(f, expect, actual, workflows)
        return True

    for variant in variants():
        yield dict(
            name=variant[0],
            task_dep=["ml_upload_cct"],
            file_dep=TASKS + WORKFLOWS + [BUILD / "tools" / "abstract.ttl"],
            targets=[destdir / f"{variant}.csv"],
            actions=[(mkdir, [destdir]), (action, variant)],
            verbosity=2
        )

def task_toolset_update():
    """Extract a toolset from concrete workflows."""

    destdir = BUILD / "tools"

    def action() -> bool:
        from rdflib import Graph
        from quangis.namespace import TOOL, bind_all
        from quangis.tools.set import ToolSet
        from quangis.workflow import Workflow
        repo = ToolSet.from_file(*TOOLS, check_integrity=True)
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
        from quangis.tools.set import ToolSet

        # TODO: this should be produced by an action itself
        repo = ToolSet.from_file(*tools, check_integrity=False)

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


def task_wf_gen_variants():
    """Generate input/output specifications to find variant workflows."""

    destdir = BUILD / "workflows" / "variants"
    apedir = BUILD / "ape"

    @functools.cache
    def generator():
        from quangis.synthesis import WorkflowGenerator
        gen = WorkflowGenerator(BUILD / "tools" / "abstract.ttl",
                BUILD / "tools" / "multi.ttl",
                DATA / "tools" / "arcgis.ttl",
            build_dir=apedir)
        return gen

    @functools.cache
    def tool_repo():
        return ToolSet.from_file(BUILD / "tools" / "abstract.ttl",
            BUILD / "tools" / "multi.ttl",
            DATA / "tools" / "arcgis.ttl", check_integrity=True)

    def action(wf_path, name, target) -> None:
        from rdflib import Graph
        from rdflib.term import Node
        from transforge.namespace import shorten
        from quangis.namespace import WFVAR, bind_all
        from quangis.workflow import Workflow
        from quangis.polytype import Polytype
        from quangis.ccd import CCD

        # Find out input and outputs of existing workflow
        wf = Workflow.from_file(wf_path)
        sources, targets = wf.io(wf.root)

        # Find every tool application that has a source as an input or a target 
        # as an output, and determine the types by looking at the types of 
        # corresponding abstract tools
        repo = tool_repo()
        all_types: dict[Node, Polytype] = dict()
        for action in wf.high_level_actions(wf.root):
            tool = repo.abstract[wf.impl(action)]
            inputs = wf.inputs_labelled(action)
            output = wf.output(action)
            for source in sources:
                for k, v in inputs.items():
                    if v == source:
                        if source not in all_types:
                            all_types[source] = tool.inputs[k].type
                        else:
                            assert all_types[source] == tool.inputs[k].type
                        # .update(tool.inputs[k].type.uris())
            target_node, = targets
            if target_node == output:
                if target_node not in all_types:
                    all_types[target_node] = tool.output.type
                else:
                    assert all_types[target_node] == tool.output.type
                # .update(tool.output.type.uris())

        # Determine the overall types and projected types
        source_types = [all_types[s] for s in sources]
        target_types = [all_types[t] for t in targets]

        p_source_types = [all_types[s].projection() for s in sources]
        p_target_types = [all_types[t].projection() for t in targets]

        # Remove the syntactic part of types
        for x in p_source_types, p_target_types:
            for i in range(len(x)):
                del x[i][CCD.LayerA]

        # Generate variants
        gen = generator()
        solutions_raw = Graph()
        for wf in gen.run(p_source_types, p_target_types, solutions=5, 
                prefix=WFVAR[shorten(wf.root)]):
            solutions_raw += wf
        bind_all(solutions_raw)
        solutions_raw.serialize(target, format="ttl")
        with open(target, 'a') as f:
            f.write("\n# Generated with APE\n# Input types:\n")
            for s, ps in zip(source_types, p_source_types):
                f.write(f"# \t{ps} [projected from {s}]\n")
            f.write("# Output types:\n")
            for t, pt in zip(target_types, p_target_types):
                f.write(f"# \t{pt} [projected from {t}]\n")

    for wf in WORKFLOWS:
        target = destdir / wf.name
        yield dict(
            name=wf.name,
            file_dep=[wf,
                BUILD / "tools" / "abstract.ttl",
                BUILD / "tools" / "multi.ttl",
                DATA / "tools" / "arcgis.ttl"],
            targets=[target],
            actions=[
                (mkdir, [apedir]),
                (mkdir, [destdir]),
                (action, [wf, wf.stem, target])],
            verbosity=2)


def task_wf_gen():
    """Hack around limitations of APE; see issue #18."""

    @functools.cache
    def tool_repo():
        return ToolSet.from_file(BUILD / "tools" / "abstract.ttl", 
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
        from rdflib.namespace import Namespace
        from transforge.namespace import TF, RDF, RDFS
        from transforge.graph import TransformationGraph
        from transforge.query import transformation2sparql
        from transforge.type import Product, TypeOperation
        from quangis.cct import cct, R3, R2, Obj, Reg
        from urllib.parse import quote_plus

        QUESTION = Namespace("https://quangis.github.io/questions#")

        with open(dependencies[0], 'r') as f:
            inputs = json.load(f)

        g = TransformationGraph(cct)
        for parsed_question in inputs:

            task = QUESTION[quote_plus(parsed_question['question'])]
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


def task_question_to_ccd():

    destdir = BUILD / "transformations" / "questionbased"
    apedir = BUILD / "ape"

    @functools.cache
    def generator():
        from quangis.synthesis import WorkflowGenerator
        gen = WorkflowGenerator(BUILD / "tools" / "abstract.ttl",
            BUILD / "tools" / "multi.ttl",
            DATA / "tools" / "arcgis.ttl", build_dir=apedir)
        return gen

    def tool_repo():
        return ToolSet.from_file(BUILD / "tools" / "abstract.ttl", 
            check_integrity=True)

    def action(source) -> None:
        from rdflib import Graph, RDF, RDFS, URIRef, Literal
        from quangis.namespace import bind_all, EX, WF, WFGEN
        from quangis.cct2ccd import cct2ccd
        from quangis.tools.set import InputHackError
        from transforge.namespace import TF, shorten
        from transforge.graph import WorkflowCompositionError

        g = Graph()
        g.parse(source, format="ttl")

        def leaves(node):
            next = list(g.objects(node, TF["from"]))
            if next:
                for n in next:
                    yield from leaves(n)
            else:
                yield node

        repo = tool_repo()

        # Generate workflows
        gen = generator()
        for task in g.subjects(RDF.type, TF.Task):
            assert isinstance(task, URIRef)

            name = shorten(task)
            out_node = g.value(task, TF.output)
            out_type = g.value(out_node, TF.type)
            in_types = [g.value(t, TF.type) for t in leaves(out_node)]
            assert isinstance(out_type, URIRef)

            out_ccd = cct2ccd(out_type)
            in_ccds = [cct2ccd(t) for t in in_types]

            for i, wf_raw in enumerate(gen.run(
                    in_ccds, [out_ccd], solutions=10, prefix=WFGEN[name])):

                wf_raw.add((wf_raw.root, TF.implements, task))
                wf_raw.add((task, TF.implementation, wf_raw.root))

                for comment in g.objects(task, RDFS.comment):
                    wf_raw.add((wf_raw.root, RDFS.comment, comment))
                wf_raw.add((wf_raw.root, RDFS.comment, Literal(
                    f"Out: {out_ccd}\nIn: \n"
                    f"{' & '.join(str(s) for s in in_ccds)}")))

                # Perform input permutation hack
                assert (None, RDF.type, WF.Workflow) in wf_raw

                invalid = False
                try:
                    wf = repo.input_permutation_hack(wf_raw)
                except InputHackError as e:
                    # TODO: Note that simply removing workflows that cannot 
                    # be input-hacked means that we will likely overlook 
                    # workflows that need e.g. two inputs of the same type
                    wf = wf_raw
                    wf.remove((wf_raw.root, RDF.type, WF.Workflow))
                    wf.add((wf_raw.root, RDF.type, WF.InvalidWorkflow))
                    wf.add((wf_raw.root, RDFS.comment, Literal(str(e))))
                    invalid = True
                else:
                    # Derive transformation graphs
                    try:
                        wf = read_transformation(wf, repo.graph())
                    except WorkflowCompositionError as e:
                        wf.remove((wf_raw.root, RDF.type, WF.Workflow))
                        wf.add((wf_raw.root, RDF.type, WF.InvalidWorkflow))
                        wf.add((wf_raw.root, RDFS.comment, Literal(str(e))))
                        invalid = True
                bind_all(wf)
                wf.serialize(
                    destdir / f"{'invalid_' if invalid else ''}{name}_{i}.ttl",
                    format="ttl")

    for qb in QUESTIONS:
        src = BUILD / "query" / f"{qb.stem}.ttl"
        yield dict(
            name=qb.stem,
            file_dep=[src],
            targets=[destdir / "marker"],
            actions=[(mkdir, [destdir]), (action, [src])]
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

        g.serialize(targets[0])

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
        task_dep=['test_unittest', 'test_toolset'],
        verbosity=2
    )

def task_test_unittest():
    """Perform unit tests for checking the code."""
    def action():
        import pytest
        pytest.main(list((ROOT / "tests").glob("test_*.py")))

    return dict(actions=[action], verbosity=2)

def task_test_toolset():
    """Check integrity of tool file."""
    def action(method) -> bool:
        repo = ToolSet.from_file(*TOOLS, check_integrity=False)
        try:
            method(repo)
        except IntegrityError:
            raise
        else:
            return True

    for attr in dir(ToolSet):
        if attr.startswith("check_"):
            yield dict(
                name=attr,
                actions=[(action, [getattr(ToolSet, attr)])],
                verbosity=2
            )
