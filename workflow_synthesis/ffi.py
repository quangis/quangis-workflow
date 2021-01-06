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

from rdf_namespaces import CCD, WF, TOOLS, setprefixes

import rdflib
from rdflib import Graph, BNode, URIRef
from rdflib.term import Node
from rdflib.namespace import RDF, Namespace
import jpype
import jpype.imports
from typing import Iterable, Tuple, Mapping, Dict

# We need version 1.1.2's API; lower versions won't work
jpype.startJVM(classpath=['lib/APE-1.1.2-executable.jar'])

import java.io
import java.util
import org.json
import nl.uu.cs.ape.sat
import nl.uu.cs.ape.sat.configuration
import nl.uu.cs.ape.sat.models
import nl.uu.cs.ape.sat.utils
import nl.uu.cs.ape.sat.core.solutionStructure


class Datatype:
    """
    A semantic datatype, in multiple dimensions.
    """

    def __init__(self, mapping: Mapping[URIRef, Iterable[URIRef]]):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """
        self._mapping = mapping

    def to_java(self,
                setup: nl.uu.cs.ape.sat.utils.APEDomainSetup,
                is_output: bool = False) -> nl.uu.cs.ape.sat.models.Type:

        obj = org.json.JSONObject()
        for dimension, subclasses in self._mapping.items():
            a = org.json.JSONArray()
            for c in subclasses:
                a.put(str(c))
            obj.put(str(dimension), a)

        return nl.uu.cs.ape.sat.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)


def _fix_typeid(typeid):
    typeid = str(typeid)
    if typeid.endswith("_plain"):
        return typeid[:-6]
    else:
        return typeid


def _fix_toolid(toolid):
    return str(toolid).strip("\"").split("[tool]")[0]


class Workflow:
    """
    A single workflow.
    """

    def __init__(self,
                 wf: nl.uu.cs.ape.sat.core.solutionStructure.SolutionWorkflow):

        self._wf: Node = BNode()
        self._graph: Graph = Graph()
        self._resources: Dict[str, Node] = {}
        setprefixes(self._graph)

        self._graph.add((self._wf, RDF.type, WF.Workflow))

        for src in wf.getWorkflowInputTypeStates():
            node = self.add_resource(src)
            self._graph.add((self._wf, WF.source, node))

        for mod in wf.getModuleNodes():
            self.add_module(mod)

    def add_module(self, mod: nl.uu.cs.ape.sat.core.solutionStructure.ModuleNode) -> Node:
        mod_node = BNode()
        tool_node = URIRef(_fix_toolid(mod.getNodeID()))

        self._graph.add((self._wf, WF.edge, mod_node))
        self._graph.add((mod_node, WF.applicationOf, tool_node))

        for src in mod.getInputTypes():
            node = self.add_resource(src)
            self._graph.add((mod_node, WF.input, node))

        for dst in mod.getOutputTypes():
            node = self.add_resource(dst)
            self._graph.add((mod_node, WF.output, node))

    def add_resource(self, type_node: nl.uu.cs.ape.sat.models.Type) -> Node:
        """
        Make sure a resource node exists and has the proper types. Return said
        node.
        """

        name = type_node.getShortNodeID()
        node = self._resources.get(name)
        if not node:
            node = self._resources[name] = BNode(name)

            for t in type_node.getTypes():
                type_node = URIRef(_fix_typeid(t.getPredicateID()))
                self._graph.add((node, RDF.type, type_node))

        return node

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
                 dimensions: Iterable[URIRef]):

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
            inputs: Iterable[Datatype],
            outputs: Iterable[Datatype],
            solution_length: Tuple[int, int] = (1, 10),
            solutions: int = 10) -> Iterable[Workflow]:

        inp = java.util.Arrays.asList(*(i.to_java(self.setup, False)
                                        for i in inputs))
        out = java.util.Arrays.asList(*(o.to_java(self.setup, True)
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
        Datatype({
            CCD.CoreConceptQ: [CCD.CoreConceptQ],
            CCD.LayerA: [CCD.LayerA],
            CCD.NominalA: [CCD.RatioA]
        }),
    ],
    outputs=[
        Datatype({
            CCD.CoreConceptQ: [CCD.CoreConceptQ],
            CCD.LayerA: [CCD.LayerA],
            CCD.NominalA: [CCD.PlainRatioA]
        })
    ]
)
for s in solutions:
    print("Solution:")
    print(s.to_rdf().serialize(format="turtle").decode("utf-8"))
