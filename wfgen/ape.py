"""
A Pythonic interface to the Automated Pipeline Explorer
<https://github.com/sanctuuary/APE> for workflow synthesis.
"""

from __future__ import annotations

import json
from pathlib import Path
from itertools import count
import typing
from typing import Iterable, Iterator
from typing_extensions import TypedDict

import jpype
import jpype.imports
from rdflib import Graph, BNode, URIRef, Literal
from rdflib.term import Node
from rdflib.namespace import Namespace, RDF, RDFS
from transformation_algebra.namespace import EX, shorten

from wfgen.types import Type
from wfgen.util import build_dir, download

MVN = "https://repo1.maven.org/maven2"
JAR = [
    f"{MVN}/io/github/sanctuuary/APE/1.1.12/APE-1.1.12-executable.jar"
    # f"{MVN}/io/github/sanctuuary/APE/2.0.3/APE-2.0.3-executable.jar"
]
jpype.startJVM(classpath=[str(download(j)) for j in JAR])

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
            namespace: Namespace, tool_root: Node, dimensions: list[Node],
            build_dir: Path = build_dir,
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
            j_io.File(str(taxonomy_file)), str(namespace), str(tool_root),
            j_util.Arrays.asList(*map(str, dimensions)),
            j_io.File(str(tools_file)), strictToolAnnotations
        )
        self.ape = j_ape.APE(self.config)
        self.setup = self.ape.getDomainSetup()

    def type(self, is_output: bool, t: Type) -> j_ape.models.Type:
        """
        Convert `Type` to the corresponding APE structure.
        """

        obj = j_json.JSONObject()
        for dimension, classes in t.items():
            array = j_json.JSONArray()
            for c in classes:
                array.put(str(c))
            obj.put(str(dimension.root), array)

        return j_ape.models.Type.taxonomyInstanceFromJson(
            obj, self.setup, is_output)

    def type_array(self, is_output: bool,
            types: Iterable[Type]) -> j_json.JSONArray:

        return j_util.Arrays.asList(*(
            self.type(is_output, t) for t in types))

    def run(self,
            inputs: Iterable[Type],
            outputs: Iterable[Type],
            names: Iterator[URIRef] = (EX[f"solution{i}"] for i in count()),
            solution_length: tuple[int, int] = (1, 10),
            solutions: int = 10,
            timeout: int = 600,
            use_workflow_input: typing.Literal["NONE", "ONE", "ALL"] = "ALL",
            output_dir: Path = Path(".")) -> Iterator[Workflow]:

        inputs = self.type_array(False, inputs)
        outputs = self.type_array(True, outputs)

        config = j_ape.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(str(output_dir))\
            .withConstraintsJSON(j_json.JSONObject())\
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

        result = self.ape.runSynthesis(config)

        for i in range(result.getNumberOfSolutions()):
            uri: URIRef = next(names)
            wf = Workflow(uri)
            wf.add_wf(result.get(i))
            yield wf


WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")


class Workflow(Graph):
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

            in_preds = (WF.input1, WF.input2, WF.input3)
            for in_pred, type in zip(in_preds, module.getInputTypes()):
                resource = self.add_resource(type)
                self.add((app, in_pred, resource))

            out_preds = (WF.output, WF.output2, WF.output3)
            for out_pred, type in zip(out_preds, module.getOutputTypes()):
                resource = self.add_resource(type)
                self.add((app, out_pred, resource))

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
