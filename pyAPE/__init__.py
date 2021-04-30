"""
This is a wrapper to APE, the Java application that is used for workflow
synthesis. It interfaces with a JVM.
"""

import os
import os.path
import tempfile
import json
import jpype
import jpype.imports
from rdflib import Graph, BNode, URIRef
from rdflib.term import Node
from rdflib.namespace import Namespace
from typing import Iterable, Tuple, Dict, List, Union
from typing_extensions import TypedDict

# We need version 1.1.5's API; lower versions won't work
CLASS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'lib', 'APE-1.1.5-executable.jar')
jpype.startJVM(classpath=[CLASS_PATH])

import java.io
import java.util
import org.json
import nl.uu.cs.ape.sat
import nl.uu.cs.ape.sat.configuration
import nl.uu.cs.ape.sat.models
import nl.uu.cs.ape.sat.utils
from nl.uu.cs.ape.sat.core.solutionStructure import \
    SolutionWorkflow, ModuleNode


ToolDict = TypedDict('ToolDict', {
    'id': str,
    'label': str,
    'inputs': List[Dict[URIRef, List[URIRef]]],
    'outputs': List[Dict[URIRef, List[URIRef]]],
    'taxonomyOperations': List[URIRef]
})

ToolsDict = TypedDict('ToolsDict', {
    'functions': List[ToolDict]
})

TypeNode = Dict[URIRef, List[URIRef]]


class Workflow:
    """
    A single solution workflow.
    """

    def __init__(self, wf: SolutionWorkflow):
        self._wf: Node = BNode()
        self._graph: Graph = Graph()
        self._resources: Dict[str, Node] = {}

        self._graph.add((self._wf, RDF.type, WF.Workflow))

        for src in wf.getWorkflowInputTypeStates():
            node = self.add_resource(src)
            self._graph.add((self._wf, WF.source, node))

        for mod in wf.getModuleNodes():
            self.add_module(mod)

    def add_module(self, mod: ModuleNode) -> Node:
        mod_node = BNode()
        tool_node = URIRef(mod.getNodeLongLabel())

        self._graph.add((self._wf, WF.edge, mod_node))
        self._graph.add((mod_node, WF.applicationOf, tool_node))

        for src in mod.getInputTypes():
            node = self.add_resource(src)
            self._graph.add((mod_node, WF.input, node))

        for dst in mod.getOutputTypes():
            node = self.add_resource(dst)
            self._graph.add((mod_node, WF.output, node))

    def add_resource(self, type_node: nl.uu.cs.ape.sat.models.Type) -> Node:
        name = type_node.getShortNodeID()
        node = self._resources.get(name)
        if not node:
            node = self._resources[name] = BNode()

            for t in type_node.getTypes():
                type_node = URIRef(t.getPredicateLongLabel())
                self._graph.add((node, RDF.type, type_node))

        return node

    def to_rdf(self) -> Graph:
        return self._graph

    @property
    def root(self) -> Node:
        return self._wf


class APE:
    def __init__(
            self,
            taxonomy: Union[str, Graph],
            tools: Union[str, ToolsDict],
            namespace: Namespace,
            tool_root: URIRef,
            dimensions: List[URIRef],
            strictToolAnnotations: bool = True):

        # Serialize if we weren't given paths
        if isinstance(taxonomy, Graph):
            fd, taxonomy_file = tempfile.mkstemp(prefix='pyAPE-', suffix='.rdf')
            with open(fd, 'w') as f:
                taxonomy.serialize(destination=f, format='xml')
        else:
            taxonomy_file = taxonomy

        if isinstance(tools, dict):
            fd, tools_file = tempfile.mkstemp(prefix='pyAPE-', suffix='.json')
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
        if taxonomy is not taxonomy_file:
            os.remove(taxonomy_file)
        if tools is not tools_file:
            os.remove(tools_file)

    def run(self,
            inputs: Iterable[TypeNode],
            outputs: Iterable[TypeNode],
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
            Workflow(result.get(i))
            for i in range(result.getNumberOfSolutions())
        ]

    def type_node(
            self,
            typenode: TypeNode,
            is_output: bool = False) -> nl.uu.cs.ape.sat.models.Type:

        setup: nl.uu.cs.ape.sat.utils.APEDomainSetup = self.setup
        obj = org.json.JSONObject()
        for dimension, classes in typenode.items():
            arr = org.json.JSONArray()
            for c in classes:
                arr.put(str(c))
            obj.put(str(dimension), arr)

        return nl.uu.cs.ape.sat.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)
