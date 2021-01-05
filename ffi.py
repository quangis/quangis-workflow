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
# -  exclusively use its CLI, which limits our freedom, wastes resources on
# every run, and requires us to make sure that RDF output capabilities are
# developed upstream or in our own fork;
# -  run a JVM bridge, as we have done --- it allows for the most flexibility

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

        solutions = self.ape.runSynthesis(config)
        return solutions

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


ape = APE2()
ape.run(
    inputs=[
        {"CoreConceptQ": ["FieldQ"], "LayerA": ["PointA"], "NominalA": ["PlainIntervalA"]},
        {"CoreConceptQ": ["ObjectQ"], "LayerA": ["VectorTessellationA"], "NominalA": ["PlainNominalA"]}
    ],
    outputs=[
        {"CoreConceptQ": ["ObjectQ"], "LayerA": ["VectorTessellationA"], "NominalA": ["IntervalA"]}
    ]
)
