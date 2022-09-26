from __future__ import annotations

import os
import os.path
import tempfile
import json
import jpype
import jpype.imports
from itertools import count
from rdflib import Graph, BNode, URIRef
from rdflib.term import Node
from rdflib.namespace import Namespace, RDF
from typing import Iterable, Tuple, Dict, List, Union, Iterator
from typing_extensions import TypedDict
from transformation_algebra.namespace import EX

import apey.data

# https://repo1.maven.org/maven2/io/github/sanctuuary/APE/2.0.3/APE-2.0.3.jar

# We need version 1.1.5's API; lower versions won't work
CLASS_PATH = apey.data.get('APE-1.1.5-executable.jar', url=(
    'https://github.com/sanctuuary/APE'
    '/releases/download/v1.1.5/APE-1.1.5-executable.jar'))
jpype.startJVM(classpath=[str(CLASS_PATH)])

# Java imports
import java.io  # noqa: E402
import java.util  # noqa: E402
import org.json  # noqa: E402
import nl.uu.cs.ape.sat  # noqa: E402
import nl.uu.cs.ape.sat.configuration  # noqa: E402
import nl.uu.cs.ape.sat.models  # noqa: E402
import nl.uu.cs.ape.sat.utils  # noqa: E402
import nl.uu.cs.ape.sat.core.solutionStructure  # noqa: E402


ToolDict = TypedDict('ToolDict', {
    'id': str,
    'label': str,
    'inputs': List[Dict[Node, List[Node]]],
    'outputs': List[Dict[Node, List[Node]]],
    'taxonomyOperations': List[Node]
})


"Type of tools, comparable to the JSON format expected by APE."
ToolsDict = TypedDict('ToolsDict', {
    'functions': List[ToolDict]
})


"Type of semantic type nodes, represented as a dictionary of rdflib nodes."
TypeNode = Dict[Node, List[Node]]


class APE(object):
    """
    An interface to JVM. After initialization, use `.run()` to run APE.
    """

    def __init__(
            self,
            taxonomy: Union[str, Graph],
            tools: Union[str, ToolsDict],
            namespace: Namespace,
            tool_root: Node,
            dimensions: List[Node],
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
        self.config = nl.uu.cs.ape.sat.configuration.APECoreConfig(
            java.io.File(taxonomy_file),
            str(namespace),
            str(tool_root),
            java.util.Arrays.asList(*map(str, dimensions)),
            java.io.File(tools_file),
            strictToolAnnotations
        )
        self.ape = nl.uu.cs.ape.sat.APE(self.config)
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
            solution_length: Tuple[int, int] = (1, 10),
            solutions: int = 10,
            timeout: int = 600) -> List[Workflow]:

        inputs = java.util.Arrays.asList(*(
            self.type_node(i, False) for i in inputs))
        outputs = java.util.Arrays.asList(*(
            self.type_node(o, True) for o in outputs))

        config = nl.uu.cs.ape.sat.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(".")\
            .withConstraintsJSON(org.json.JSONObject())\
            .withSolutionMinLength(solution_length[0])\
            .withSolutionMaxLength(solution_length[1])\
            .withMaxNoSolutions(solutions)\
            .withTimeoutSec(timeout)\
            .withProgramInputs(inputs)\
            .withProgramOutputs(outputs)\
            .withApeDomainSetup(self.setup)\
            .build()

        result = self.ape.runSynthesis(config)

        return [
            Workflow(result.get(i), root=next(names))
            for i in range(result.getNumberOfSolutions())
        ]

    def type_node(
            self,
            typenode: TypeNode,
            is_output: bool = False) -> nl.uu.cs.ape.sat.models.Type:
        """
        Convert dictionary representing a semantic type to the Java objects
        defined .
        """

        setup: nl.uu.cs.ape.sat.utils.APEDomainSetup = self.setup
        obj = org.json.JSONObject()
        for dimension, classes in typenode.items():
            arr = org.json.JSONArray()
            for c in classes:
                arr.put(str(c))
            obj.put(str(dimension), arr)

        return nl.uu.cs.ape.sat.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)


WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")


class Workflow(Graph):
    """
    A single solution workflow represented as an RDF graph in the
    http://geographicknowledge.de/vocab/Workflow.rdf# namespace.
    """

    def __init__(
            self,
            java_wf: nl.uu.cs.ape.sat.core.solutionStructure.SolutionWorkflow,
            root: URIRef):
        """
        Create RDF graph from Java object.
        """

        super().__init__()

        self.root: Node = root
        self.resources: Dict[str, Node] = {}
        self.add((self.root, RDF.type, WF.Workflow))

        for src in java_wf.getWorkflowInputTypeStates():
            node = self.add_resource(src)
            self.add((self.root, WF.source, node))

        for mod in java_wf.getModuleNodes():
            self.add_module(mod)

    def add_module(
            self,
            mod: nl.uu.cs.ape.sat.core.solutionStructure.ModuleNode) -> Node:
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

    def add_resource(self, type_node: nl.uu.cs.ape.sat.models.Type) -> Node:
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
