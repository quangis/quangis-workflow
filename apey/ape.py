"""
A Pythonic interface to the Automated Pipeline Explorer
<https://github.com/sanctuuary/APE> for workflow synthesis.
"""

from __future__ import annotations

import sys
import os
import os.path
import tempfile
import json
import urllib
import jpype
import jpype.imports
from pathlib import Path
from itertools import count
from rdflib import Graph, BNode, URIRef
from rdflib.term import Node
from rdflib.namespace import Namespace, RDF
from typing import Iterable, Iterator
from typing_extensions import TypedDict
from transformation_algebra.namespace import EX


def data(filename: str, url: str | None = None) -> Path:
    """
    Get a file from the directory where we store application-specific data
    files, or download it if it's not present.
    """

    if sys.platform.startswith("win"):
        path = Path(os.getenv("LOCALAPPDATA"))
    elif sys.platform.startswith("darwin"):
        path = Path("~/Library/Application Support")
    elif sys.platform.startswith("linux"):
        path = Path(os.getenv("XDG_DATA_HOME", "~/.local/share"))
    else:
        raise RuntimeError("Unsupported platform")

    path = Path(path).expanduser() / "apey" / filename

    try:
        path.mkdir(parents=True)
    except FileExistsError:
        pass

    if not path.exists():
        if url:
            print(
                f"Could not find data file {path}; now downloading from {url}",
                file=sys.stderr)
            urllib.request.urlretrieve(url, filename=path)
        else:
            raise FileNotFoundError

    return path


# https://repo1.maven.org/maven2/io/github/sanctuuary/APE/2.0.3/APE-2.0.3.jar
# We need version 1.1.5's API; lower versions won't work
CLASS_PATH = data('APE-1.1.5-executable.jar', url=(
    'https://github.com/sanctuuary/APE'
    '/releases/download/v1.1.5/APE-1.1.5-executable.jar'))
jpype.startJVM(classpath=[str(CLASS_PATH)])

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


"Type of semantic type nodes, represented as a dictionary of rdflib nodes."
TypeNode = dict[Node, list[Node]]


class APE(object):
    """
    An interface to JVM. After initialization, use `.run()` to run APE.
    """

    def __init__(
            self,
            taxonomy: str | Graph,
            tools: str | ToolsDict,
            namespace: Namespace,
            tool_root: Node,
            dimensions: list[Node],
            strictToolAnnotations: bool = True):

        # Serialize if we weren't given paths
        if isinstance(taxonomy, Graph):
            fd, taxonomy_file = tempfile.mkstemp(prefix='apey-', suffix='.rdf')
            taxonomy.serialize(destination=taxonomy_file, format='xml')
        else:
            taxonomy_file = taxonomy

        if isinstance(tools, dict):
            fd, tools_file = tempfile.mkstemp(prefix='apey-', suffix='.json')
            with open(fd, 'w') as f:
                json.dump(tools, f)
        else:
            tools_file = tools

        # Set up APE in JVM
        self.config = j_ape.configuration.APECoreConfig(
            j_io.File(taxonomy_file),
            str(namespace),
            str(tool_root),
            j_util.Arrays.asList(*map(str, dimensions)),
            j_io.File(tools_file),
            strictToolAnnotations
        )
        self.ape = j_ape.APE(self.config)
        self.setup = self.ape.getDomainSetup()

        # Safe to delete since APE should have read the files now
        if taxonomy != taxonomy_file:
            os.remove(taxonomy_file)
        if tools != tools_file:
            os.remove(tools_file)

    def run(self,
            inputs: Iterable[TypeNode],
            outputs: Iterable[TypeNode],
            names: Iterator[URIRef] = (EX[f"solution{i}"] for i in count()),
            solution_length: tuple[int, int] = (1, 10),
            solutions: int = 10,
            timeout: int = 600) -> Iterator[Workflow]:

        inputs = j_util.Arrays.asList(*(
            self.type_node(i, False) for i in inputs))
        outputs = j_util.Arrays.asList(*(
            self.type_node(o, True) for o in outputs))

        config = j_ape.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(".")\
            .withConstraintsJSON(j_json.JSONObject())\
            .withSolutionMinLength(solution_length[0])\
            .withSolutionMaxLength(solution_length[1])\
            .withMaxNoSolutions(solutions)\
            .withTimeoutSec(timeout)\
            .withProgramInputs(inputs)\
            .withProgramOutputs(outputs)\
            .withApeDomainSetup(self.setup)\
            .build()

        result = self.ape.runSynthesis(config)

        for i in range(result.getNumberOfSolutions()):
            uri: URIRef = next(names)
            ape_wf: j_ape.core.solutionStructure.SolutionWorkflow = result.get(i)
            yield Workflow(ape_wf, root=uri)

    def type_node(
            self,
            typenode: TypeNode,
            is_output: bool = False) -> j_ape.models.Type:
        """
        Convert dictionary representing a semantic type to the Java objects
        defined .
        """

        setup: j_ape.utils.APEDomainSetup = self.setup
        obj = j_json.JSONObject()
        for dimension, classes in typenode.items():
            arr = j_json.JSONArray()
            for c in classes:
                arr.put(str(c))
            obj.put(str(dimension), arr)

        return j_ape.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)


WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")


class Workflow(Graph):
    """
    A single solution workflow represented as an RDF graph in the
    http://geographicknowledge.de/vocab/Workflow.rdf# namespace.
    """

    def __init__(
            self,
            java_wf: j_ape.core.solutionStructure.SolutionWorkflow,
            root: URIRef):
        """
        Create RDF graph from Java object.
        """

        super().__init__()

        self.root: Node = root
        self.resources: dict[str, Node] = {}
        self.add((self.root, RDF.type, WF.Workflow))

        for src in java_wf.getWorkflowInputTypeStates():
            node = self.add_resource(src)
            self.add((self.root, WF.source, node))

        for mod in java_wf.getModuleNodes():
            self.add_module(mod)

    def add_module(
            self,
            mod: j_ape.core.solutionStructure.ModuleNode) -> Node:
        """
        Add a blank node representing a tool module to the RDF graph, and
        return it.
        """
        mod_node = BNode()
        tool_node = URIRef(mod.getNodeLongLabel())

        self.add((self.root, WF.edge, mod_node))
        self.add((mod_node, WF.applicationOf, tool_node))

        for src in mod.getInputTypes():
            node = self.add_resource(src)
            self.add((mod_node, WF.input, node))

        for dst in mod.getOutputTypes():
            node = self.add_resource(dst)
            self.add((mod_node, WF.output, node))

        return mod_node

    def add_resource(self, type_node: j_ape.models.Type) -> Node:
        """
        Add a blank node representing a resource of the given type to the RDF
        graph, and return it.
        """
        name = type_node.getShortNodeID()
        node = self.resources.get(name)
        if not node:
            node = self.resources[name] = BNode()
            for t in type_node.getTypes():
                type_node = URIRef(t.getPredicateLongLabel())
                self.add((node, RDF.type, type_node))
        return node
