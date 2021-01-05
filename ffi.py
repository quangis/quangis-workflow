"""
This is a FFI to APE.
Connect to APE Java
"""

import jpype
import jpype.imports
from jpype.types import JString

jpype.startJVM(classpath=['lib/APE-1.1.2-executable.jar'])

from java.io import File
from java.util import Arrays
from nl.uu.cs.ape.sat import APE
from nl.uu.cs.ape.sat.configuration import APECoreConfig, APERunConfig
from nl.uu.cs.ape.sat.utils import APEDomainSetup
from org.json import JSONObject

print(jpype.isJVMStarted())

config = APECoreConfig(
    File("build/GISTaxonomy.rdf"),
    JString("http://geographicknowledge.de/vocab/CoreConceptData.rdf#"),
    JString("http://geographicknowledge.de/vocab/GISTools.rdf#Tool"),
    Arrays.asList("CoreConceptQ", "LayerA", "NominalA"),
    File("build/ToolDescription.json"),
    True
)

ape = APE(config)
setup = APEDomainSetup(config)
print(setup)

run = APERunConfig\
    .builder()\
    .withSolutionDirPath("build")\
    .withConstraintsJSON(JSONObject())\
    .withSolutionMinLength(1)\
    .withSolutionMaxLength(10)\
    .withMaxNoSolutions(100)\
    .withApeDomainSetup(setup)\
    .build()

solutions = ape.runSynthesis(run)
