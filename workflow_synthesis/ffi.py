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
from rdflib import BNode, URIRef, Graph
from rdflib.namespace import RDF, Namespace
import jpype
import jpype.imports
from typing import Iterable, Tuple, Mapping

# We need version 1.1.2's API; lower versions won't work
jpype.startJVM(classpath=['lib/APE-1.1.2-executable.jar'])

from java.io import File
from java.util import Arrays
from org.json import JSONObject, JSONArray
import nl.uu.cs.ape.sat
import nl.uu.cs.ape.sat.configuration
import nl.uu.cs.ape.sat.models
import nl.uu.cs.ape.sat.utils
from nl.uu.cs.ape.sat.core.solutionStructure import SolutionWorkflow


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

        obj = JSONObject()
        for dimension, subclasses in self._mapping.items():
            a = JSONArray()
            for c in subclasses:
                a.put(str(c))
            obj.put(str(dimension), a)

        return nl.uu.cs.ape.sat.models.Type.taxonomyInstanceFromJson(
            obj, setup, is_output)


class Workflow:
    """
    A single workflow.
    """

    def __init__(self, wf: SolutionWorkflow):
        """
        Internally, we just store APE's SolutionWorkflow.
        """
        self._wf = wf

    def to_rdf(self):
        """
        Represent as an RDF graph.
        """
        pass


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
            File(taxonomy),
            str(namespace),
            str(tool_root),
            Arrays.asList(*map(str, dimensions)),
            File(tools),
            True
        )
        self.ape = nl.uu.cs.ape.sat.APE(self.config)
        self.setup = self.ape.getDomainSetup()

    def run(self,
            inputs: Iterable[Datatype],
            outputs: Iterable[Datatype],
            solution_length: Tuple[int, int] = (1, 10),
            max_solutions: int = 100) -> Iterable[Graph]:

        inp = Arrays.asList(*(i.to_java(self.setup, False) for i in inputs))
        out = Arrays.asList(*(o.to_java(self.setup, True) for o in outputs))

        config = nl.uu.cs.ape.sat.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath(".")\
            .withConstraintsJSON(JSONObject())\
            .withSolutionMinLength(solution_length[0])\
            .withSolutionMaxLength(solution_length[1])\
            .withMaxNoSolutions(max_solutions)\
            .withProgramInputs(inp)\
            .withProgramOutputs(out)\
            .withApeDomainSetup(self.setup)\
            .build()

        solutions = self.ape.runSynthesis(config)

        return [
            workflow_as_rdf(solutions.get(i))
            for i in range(0, solutions.getNumberOfSolutions())
        ]


def resource_node(t, g, resources):
    """
    Make sure a resource node exists and has the proper types.

    @param t: The Java TypeNode provided by APE.
    @param g: The RDF graph in which to assigne the resource
    @param resources: A mapping keeping track of which resources we have seen
        before.
    """

    name = t.getShortNodeID()
    node = resources.get(name)
    if not node:
        node = resources[name] = BNode(name)

        for datatype in t.getTypes():
            type_uri = fix_typeid(datatype.getPredicateID())
            type_node = URIRef(type_uri)
            g.add((node, RDF.type, type_node))

    return node


def workflow_as_rdf(workflow):
    """
    Transform APE's SolutionWorkFlow into a workflow in the RDF format we
    expect.
    """

    g = rdflib.Graph()
    setprefixes(g)

    # Workflow itself
    wf = BNode()
    g.add((wf, RDF.type, WF.Workflow))

    # Mapping of data instances to input/output nodes
    resources = {}

    # Assign all source nodes
    for src in workflow.getWorkflowInputTypeStates():
        node = resource_node(src, g, resources)
        g.add((wf, WF.source, node))

    # Assign all tool nodes
    for mod in workflow.getModuleNodes():
        mod_node = BNode()
        tool_id = mod.getNodeID()
        tool_node = URIRef(fix_toolid(tool_id))

        g.add((wf, WF.edge, mod_node))
        g.add((mod_node, WF.applicationOf, tool_node))

        for src in mod.getInputTypes():
            node = resource_node(src, g, resources)
            g.add((mod_node, WF.input, node))

        for dst in mod.getOutputTypes():
            node = resource_node(dst, g, resources)
            g.add((mod_node, WF.output, node))

    print(g.serialize(format="turtle").decode("utf-8"))

    return g


def fix_typeid(typeid):
    typeid = str(typeid)
    if typeid.endswith("_plain"):
        return typeid[:-6]
    else:
        return typeid


def fix_toolid(toolid):
    return str(toolid).strip("\"").split("[tool]")[0]


ape = APE(
    taxonomy="build/GISTaxonomy.rdf",
    tools="build/ToolDescription.json",
    tool_root=TOOLS.Tool,
    namespace=CCD,
    dimensions=(CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA)
)
ape.run(
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

