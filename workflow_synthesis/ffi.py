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
from rdflib import BNode, URIRef, Literal
from rdflib.namespace import RDFS, RDF, OWL
import logging
import jpype
import jpype.imports
from jpype.types import JString

# We need version 1.1.2's API; lower versions won't work
jpype.startJVM(classpath=['lib/APE-1.1.2-executable.jar'])

from java.io import File
from java.util import Arrays
from org.json import JSONObject, JSONArray
from nl.uu.cs.ape.sat import APE
from nl.uu.cs.ape.sat.configuration import APECoreConfig, APERunConfig
from nl.uu.cs.ape.sat.utils import APEDomainSetup
from nl.uu.cs.ape.sat.models import Type


class APE2:

    def __init__(self):
        self.config = APECoreConfig(
            File("build/GISTaxonomy.rdf"),
            JString("http://geographicknowledge.de/vocab/CoreConceptData.rdf#"),
            JString("http://geographicknowledge.de/vocab/GISTools.rdf#Tool"),
            Arrays.asList(*map(JString, ["CoreConceptQ", "LayerA", "NominalA"])),
            File("build/ToolDescription.json"),
            True
        )
        self.ape = APE(self.config)
        self.setup = self.ape.getDomainSetup()

        #debug

        types = self.setup.getAllTypes()
        print(types.getDataTaxonomyDimensionIDs())
        print(types.getDataTaxonomyDimensions())
        print(types.getRootPredicates())
        print(types.size())


    def run(self, inputs, outputs):

        inputs_ = Arrays.asList(*map(self.as_type, inputs))
        outputs_ = Arrays.asList(*map(self.as_type, outputs))

        config = APERunConfig\
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


def workflow_as_rdf(workflow):
    """
    Transform APE's SolutionWorkFlow into a workflow in the RDF format we
    expect.
    """

    rdf = rdflib.Graph()
    setprefixes(rdf)

    # Workflow itself
    wf = BNode()
    rdf.add((wf, RDF.type, WF.Workflow))

    # Mapping of data instances to input/output nodes
    data = {}

    # Assign all source nodes
    for src in workflow.getWorkflowInputTypeStates():
        src_id = src.getShortNodeID()
        src_node = BNode(src_id)
        data[src_id] = src_node

        rdf.add((wf, WF.source, src_node))

        for datatype in src.getTypes():
            type_uri = fix_typeid(datatype.getPredicateID())
            type_node = URIRef(type_uri)
            rdf.add((src_node, RDF.type, type_node))
            rdf.add((src_node, RDF.type, WF.Resource))

    # Assign all tool nodes
    for mod in workflow.getModuleNodes():
        mod_node = BNode()
        tool_id = mod.getNodeID()
        tool_node = URIRef(fix_toolid(tool_id))

        rdf.add((wf, WF.edge, mod_node))
        rdf.add((mod_node, WF.applicationOf, tool_node))

        for src in mod.getInputTypes():
            src_id = src.getShortNodeID()
            src_node = data.get(src_id)
            if not src_node:
                src_node = data[src_id] = BNode(src_id)
            rdf.add((mod_node, WF.input, src_node))

            for datatype in src.getTypes():
                type_uri = fix_typeid(datatype.getPredicateID())
                type_node = URIRef(type_uri)
                rdf.add((src_node, RDF.type, type_node))

        for dst in mod.getOutputTypes():
            dst_id = dst.getShortNodeID()
            dst_node = data.get(dst_id)
            if not dst_node:
                dst_node = data[dst_id] = BNode(dst_id)
            rdf.add((mod_node, WF.output, dst_node))

            for datatype in dst.getTypes():
                type_uri = fix_typeid(datatype.getPredicateID())
                type_node = URIRef(type_uri)
                rdf.add((dst_node, RDF.type, type_node))

    print(rdf.serialize(format="turtle").decode("utf-8"))

    return rdf


def fix_typeid(typeid):
    typeid = str(typeid)
    if typeid.endswith("_plain"):
        return typeid[:-6]
    else:
        return typeid


def fix_toolid(toolid):
    return str(toolid).strip("\"").split("[tool]")[0]


ape = APE2()
ape.run(
    inputs=[
        {"CoreConceptQ": ["CoreConceptQ"], "LayerA": ["LayerA"], "NominalA":
            ["RatioA"]},
    ],
    outputs=[
        {"CoreConceptQ": ["CoreConceptQ"], "LayerA": ["LayerA"], "NominalA":
            ["PlainRatioA"]}
    ]
)


#    inputs=[
#        {"CoreConceptQ": ["FieldQ"], "LayerA": ["PointA"], "NominalA": ["PlainIntervalA"]},
#        {"CoreConceptQ": ["ObjectQ"], "LayerA": ["VectorTessellationA"], "NominalA": ["PlainNominalA"]}
#    ],
#    outputs=[
#        {"CoreConceptQ": ["ObjectQ"], "LayerA": ["VectorTessellationA"], "NominalA": ["IntervalA"]}
#    ]
