"""
This is a wrapper to APE, the Java application that is used for workflow
synthesis. 
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
from rdflib import BNode, URIRef
from rdflib.namespace import RDF
import jpype
import jpype.imports
from jpype.types import JString

# We need version 1.1.2's API; lower versions won't work
jpype.startJVM(classpath=['lib/APE-1.1.2-executable.jar'])

from java.io import File
from java.util import Arrays
from org.json import JSONObject, JSONArray
import nl.uu.cs.ape.sat
import nl.uu.cs.ape.sat.configuration
from nl.uu.cs.ape.sat.models import Type


class APE:

    def __init__(self):
        self.config = nl.uu.cs.ape.sat.configuration.APECoreConfig(
            File("build/GISTaxonomy.rdf"),
            "http://geographicknowledge.de/vocab/CoreConceptData.rdf#",
            "http://geographicknowledge.de/vocab/GISTools.rdf#Tool",
            Arrays.asList("CoreConceptQ", "LayerA", "NominalA"),
            File("build/ToolDescription.json"),
            True
        )
        self.ape = nl.uu.cs.ape.sat.APE(self.config)
        self.setup = self.ape.getDomainSetup()

    def run(self, inputs, outputs):

        inputs_ = Arrays.asList(*map(self.as_type, inputs))
        outputs_ = Arrays.asList(*map(self.as_type, outputs))

        config = nl.uu.cs.ape.sat.configuration.APERunConfig\
            .builder()\
            .withSolutionDirPath("build/")\
            .withConstraintsJSON(JSONObject())\
            .withSolutionMinLength(1)\
            .withSolutionMaxLength(10)\
            .withMaxNoSolutions(100)\
            .withProgramInputs(inputs_)\
            .withProgramOutputs(outputs_)\
            .withApeDomainSetup(self.setup)\
            .build()

        jsolutions = self.ape.runSynthesis(config)

        return [
            workflow_as_rdf(jsolutions.get(i))
            for i in range(0, jsolutions.getNumberOfSolutions())
        ]

    def as_type(self, mapping):
        """
        Turn a dictionary into an input/output Type for APE.
        """
        obj = JSONObject()
        for k, v in mapping.items():
            a = JSONArray()
            for s in v:
                a.put(JString(s))
            obj.put(JString(k), a)
        return Type.taxonomyInstanceFromJson(obj, self.setup, False)


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


ape = APE()
ape.run(
    inputs=[
        {
            "CoreConceptQ": ["CoreConceptQ"],
            "LayerA": ["LayerA"],
            "NominalA": ["RatioA"]
        },
    ],
    outputs=[
        {
            "CoreConceptQ": ["CoreConceptQ"],
            "LayerA": ["LayerA"],
            "NominalA": ["PlainRatioA"]
        }
    ]
)


