"""
A Pythonic interface to the Automated Pipeline Explorer
<https://github.com/sanctuuary/APE> for workflow synthesis.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
import typing
from typing import Iterable, Iterator
from typing_extensions import TypedDict
import urllib.request

import jpype
import jpype.imports
from platformdirs import user_cache_dir
from rdflib import Graph, BNode, URIRef, Literal
from rdflib.term import Node
from rdflib.namespace import Namespace, RDF, RDFS
from transforge.namespace import EX, shorten

from quangis.polytype import Polytype

# def start_ape(version="2.1.5") -> None:
def start_ape(version="1.1.12") -> None:
    name = f"APE-{version}-executable.jar"

    # Ensure that the APE JAR is available
    repo = "https://repo1.maven.org/maven2"
    url = f"{repo}/io/github/sanctuuary/APE/{version}/{name}"
    cache_dir = Path(user_cache_dir("quangis", "quangis"))
    path = cache_dir / name
    if not path.exists():
        print(f"{path} not found; now downloading from {url}", file=sys.stderr)
        cache_dir.mkdir(exist_ok=True)
        urllib.request.urlretrieve(url, filename=path)

    # Start it
    jpype.startJVM(classpath=[str(path)])


start_ape()

# Java imports
import java.io as j_io  # noqa: E402
import java.util as j_util  # noqa: E402
import org.json as j_json  # noqa: E402
import nl.uu.cs.ape.sat as j_ape  # noqa: E402


ToolDict = TypedDict('ToolDict', {
    'id': str,
    'label': str,
    'inputs': list[dict[Node, list[Node]]],
    'outputs': list[dict[Node, list[Node]]],
    'taxonomyOperations': list[Node]
})


"Type of tools, comparable to the JSON format expected by APE."
ToolsDict = TypedDict('ToolsDict', {
    'functions': list[ToolDict]
})


class APE(object):
    """
    An interface to JVM. After initialization, use `.run()` to run APE.
    """

    def __init__(self, taxonomy: Path | Graph, tools: Path | ToolsDict,
            ontology_prefix_iri: str, tool_root: Node, dimensions: list[Node],
            build_dir: Path = Path("."),
            strictToolAnnotations: bool = True):

        # Serialize if we weren't given paths
        if isinstance(taxonomy, Graph):
            taxonomy_file = build_dir / "taxonomy.rdf"
            taxonomy.serialize(destination=taxonomy_file, format='xml')
        else:
            taxonomy_file = taxonomy

        if isinstance(tools, dict):
            tools_file = build_dir / "tools.json"
            with open(tools_file, 'w') as f:
                json.dump(tools, f, indent=4)
        else:
            tools_file = tools

        # Set up APE in JVM
        self.config = j_ape.configuration.APECoreConfig(
            j_io.File(str(taxonomy_file)),  # ontology
            str(ontology_prefix_iri),  # ontologyPrefixIRI
            str(tool_root),  # toolTaxonomyRoot
            j_util.Arrays.asList(*map(str, dimensions)),  # dataDimensionsRoots
            j_io.File(str(tools_file)),  # toolAnnotations
            strictToolAnnotations  # strictToolAnnotations
        )
        self.ape = j_ape.APE(self.config)
        self.setup = self.ape.getDomainSetup()

    def json_type(self, t: Polytype) -> j_json.Object:
        obj = j_json.JSONObject()
        for dimension, classes in t.items():
            array = j_json.JSONArray()
            for c in classes:
                array.put(str(c))
            obj.put(str(dimension), array)
        return obj

    def type(self, is_output: bool, t: Polytype) -> j_ape.models.Type:
        """Convert `Polytype` to the corresponding APE structure."""

        return j_ape.models.Type.taxonomyInstanceFromJson(
            self.json_type(t), self.setup, is_output)

    def constraint(self, use_t: Iterable[Polytype]) -> j_json.JSONObject:
        """Add the 'use_t' constraint for the given types."""
        # TODO: Make a 'real' Constraint wrapper for other types of 
        # constraints. Just rushing through things atm
        result = j_json.JSONObject()
        constraints = j_json.JSONArray()
        for pt in use_t:
            obj = j_json.JSONObject()
            obj.put("constraintid", "use_t")
            types = j_json.JSONArray()
            types.put(self.json_type(pt))
            obj.put("parameters", types)
            constraints.put(obj)
        result.put("constraints", constraints)
        return result

    def type_array(self, is_output: bool,
            types: Iterable[Polytype]) -> j_json.JSONArray:

        return j_util.Arrays.asList(*(
            self.type(is_output, t) for t in types))

    def run(self,
            inputs: Iterable[Polytype],
            outputs: Iterable[Polytype],
            prefix: URIRef = EX["solution"],
            solution_length: tuple[int, int] = (1, 10),
            solutions: int = 10,
            timeout: int = 600,
            use_workflow_input: typing.Literal["NONE", "ONE", "ALL"] = "ALL",
            constraints: j_json.JSONObject = j_json.JSONObject(),
            output_dir: Path = Path(".")) -> Iterator[Graph]:

        inputs = self.type_array(False, inputs)
        outputs = self.type_array(True, outputs)

        config = j_ape.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(str(output_dir))\
            .withConstraintsJSON(constraints)\
            .withSolutionMinLength(solution_length[0])\
            .withSolutionMaxLength(solution_length[1])\
            .withMaxNoSolutions(solutions)\
            .withTimeoutSec(timeout)\
            .withProgramInputs(inputs)\
            .withProgramOutputs(outputs)\
            .withApeDomainSetup(self.setup)\
            .withUseWorkflowInput(getattr(j_ape.models.enums.ConfigEnum,
                use_workflow_input))\
            .build()

        print("Building for", prefix, file=sys.stderr)
        print("With constraints:", constraints, file=sys.stderr)

        result = self.ape.runSynthesis(config)

        for i in range(result.getNumberOfSolutions()):
            uri: URIRef = prefix + str(i + 1)
            wf = _Workflow(uri)
            wf.add_wf(result.get(i))
            yield wf


WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")


class _Workflow(Graph):
    """
    A single solution workflow represented as an RDF graph in the
    <http://geographicknowledge.de/vocab/Workflow.rdf#> namespace.
    """

    def __init__(self, root: URIRef):
        """
        Create RDF graph from Java object.
        """

        super().__init__()

        # Map APE's tool applications and resources to RDF ones
        self.root: Node = root
        self.apps: dict[j_ape.core.solutionStructure.ModuleNode, Node] = dict()
        self.resources: dict[j_ape.models.Type, Node] = dict()

    def add_wf(self, workflow: j_ape.core.solutionStructure.SolutionWorkflow):
        self.add((self.root, RDF.type, WF.Workflow))

        for source in workflow.getWorkflowInputTypeStates():
            node = self.add_resource(source)
            self.add((self.root, WF.source, node))

        for module in workflow.getModuleNodes():
            self.add_app(module)

    def add_app(self, module: j_ape.core.solutionStructure.ModuleNode) -> Node:
        """
        Add a blank node representing a tool module to the RDF graph, and
        return it.
        """

        try:
            return self.apps[module]
        except KeyError:
            app = BNode()
            tool = URIRef(module.getNodeLongLabel())

            self.add((self.root, WF.edge, app))
            self.add((app, WF.applicationOf, tool))

            for type in module.getInputTypes():
                resource = self.add_resource(type)
                self.add((app, WF.inputx, resource))

            for type in module.getOutputTypes():
                # Workaround: there's often an empty output for some reason
                if not list(type.getTypes()):
                    break
                resource = self.add_resource(type)
                self.add((app, WF.output, resource))

            return app

    def add_resource(self, type: j_ape.models.Type) -> Node:
        """
        Add a blank node representing a resource of the given type to the RDF
        graph, and return it.
        """
        try:
            return self.resources[type]
        except KeyError:
            resource = self.resources[type] = BNode()
            type_labels = []
            for t in type.getTypes():
                type_node = URIRef(t.getPredicateLongLabel())
                type_labels.append(shorten(type_node))
                self.add((resource, RDF.type, type_node))
            self.add((resource, RDFS.label, Literal(", ".join(type_labels))))
            return resource
