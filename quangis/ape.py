"""
This is a wrapper to APE, the Java application that is used for workflow
synthesis. It interfaces with a JVM.
"""
# This approach was chosen because we need to:
# -  run multiple solutions one after another
# -  get output workflows in RDF format
#
# APE's Java API forces us to either:
# -  switch to Java ourselves, which introduces cognitive load and extra tools
# in our pipeline;
# -  use its CLI, which limits our freedom, wastes resources on every run,
# makes us lose error handling, and requires us to make sure that RDF output
# capabilities are developed upstream or in our own fork;
# -  run a JVM bridge, as we have done --- it allows for the most flexibility

from rdflib import Graph, BNode, URIRef
from rdflib.term import Node
from rdflib.namespace import RDF, Namespace
import jpype
import jpype.imports
import os.path
from typing import Iterable, Tuple, Dict, List

from namespace import CCD, WF, TOOLS
from semtype import SemType
from ontology import Ontology

# We need version 1.1.2's API; lower versions won't work
CLASS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'lib', 'APE-1.1.2-executable.jar')
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


class Workflow:
    """
    A single workflow.
    """

    def __init__(self, wf: SolutionWorkflow):
        self._wf: Node = BNode()
        self._graph: Graph = Ontology()
        self._resources: Dict[str, Node] = {}

        self._graph.add((self._wf, RDF.type, WF.Workflow))

        for src in wf.getWorkflowInputTypeStates():
            node = self.add_resource(src)
            self._graph.add((self._wf, WF.source, node))

        for mod in wf.getModuleNodes():
            self.add_module(mod)

    def add_module(self, mod: ModuleNode) -> Node:
        mod_node = BNode()
        tool_node = Workflow.tool_node(mod.getNodeID())

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
                type_node = Workflow.type_node(t.getPredicateID())
                self._graph.add((node, RDF.type, type_node))

        return node

    @staticmethod
    def type_node(typeid: str) -> Node:
        # TODO figure out why type IDs do not correspond exactly to RDF nodes
        typeid = str(typeid)
        if typeid.endswith("_plain"):
            typeid = typeid[:-6]
        return URIRef(typeid)

    @staticmethod
    def tool_node(toolid: str) -> Node:
        # TODO figure out why tool IDs do not correspond exactly to RDF nodes
        return URIRef(str(toolid).strip("\"").split("[tool]")[0])

    def to_rdf(self) -> Graph:
        return self._graph

    @property
    def root(self) -> Node:
        return self._wf


class APE:
    """
    Wrapper class for APE.
    """

    def __init__(self,
                 taxonomy: str,
                 tools: str,
                 namespace: Namespace,
                 tool_root: URIRef,
                 dimensions: List[URIRef]):

        self.config = nl.uu.cs.ape.sat.configuration.APECoreConfig(
            java.io.File(taxonomy),
            str(namespace),
            str(tool_root),
            java.util.Arrays.asList(*map(str, dimensions)),
            java.io.File(tools),
            True
        )
        self.ape = nl.uu.cs.ape.sat.APE(self.config)
        self.setup = self.ape.getDomainSetup()

    def run(self,
            inputs: Iterable[SemType],
            outputs: Iterable[SemType],
            solution_length: Tuple[int, int] = (1, 10),
            solutions: int = 10) -> List[Workflow]:

        inp = java.util.Arrays.asList(*(self.type_node(i, False)
                                        for i in inputs))
        out = java.util.Arrays.asList(*(self.type_node(o, True)
                                        for o in outputs))

        config = nl.uu.cs.ape.sat.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(".")\
            .withConstraintsJSON(org.json.JSONObject())\
            .withSolutionMinLength(solution_length[0])\
            .withSolutionMaxLength(solution_length[1])\
            .withMaxNoSolutions(solutions)\
            .withProgramInputs(inp)\
            .withProgramOutputs(out)\
            .withApeDomainSetup(self.setup)\
            .build()

        result = self.ape.runSynthesis(config)

        return [
            Workflow(result.get(i))
            for i in range(0, result.getNumberOfSolutions())
        ]

    def type_node(self,
                  t: SemType,
                  is_output: bool = False) -> nl.uu.cs.ape.sat.models.Type:

        setup: nl.uu.cs.ape.sat.utils.APEDomainSetup = self.setup
        obj = org.json.JSONObject()
        for dimension, subclasses in t.mapping.items():
            arr = org.json.JSONArray()
            for c in subclasses:
                arr.put(str(c))
            obj.put(str(dimension), arr)

        return nl.uu.cs.ape.sat.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)


if __name__ == "__main__":
    ape = APE(
        taxonomy="build/GISTaxonomy.rdf",
        tools="build/ToolDescription.json",
        tool_root=TOOLS.Tool,
        namespace=CCD,
        dimensions=(CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA)
    )
    solutions = ape.run(
        solutions=10,
        inputs=[
            SemType({
                CCD.CoreConceptQ: [CCD.CoreConceptQ],
                CCD.LayerA: [CCD.LayerA],
                CCD.NominalA: [CCD.RatioA]
            }),
        ],
        outputs=[
            SemType({
                CCD.CoreConceptQ: [CCD.CoreConceptQ],
                CCD.LayerA: [CCD.LayerA],
                CCD.NominalA: [CCD.PlainRatioA]
            })
        ]
    )
    for s in solutions:
        print("Solution:")
        print(s.to_rdf().serialize(format="turtle").decode("utf-8"))
