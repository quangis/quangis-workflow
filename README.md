# quangis-workflow-synthesis

This repository contains the implementation for workflow synthesis in 
the [QuAnGIS](https://questionbasedanalysis.com/) project. The program 
generates possible GIS workflows from a specification of possible [GIS 
tools][tools] using the [Automated Pipeline Explorer][ape].


# Usage

The tool's inputs and outputs must be annotated with core concept 
datatypes according to the [CCD][ccd] ontology. This is translated to a 
format that APE understands, and ran in a JVM via [JPype][jpype].

The tool specification must also contains a description of their 
functionality, by means of a [CCT][cct] expression in which those inputs 
and outputs occur as variables.

Example run:

    python3 -m quangis

To run tests, simply run `nose2`.


[ccd]: http://geographicknowledge.de/vocab/CoreConceptData.rdf
[jpype]: https://jpype.readthedocs.io/
[ape]: https://github.com/sanctuuary/APE
[aped]: https://ape-framework.readthedocs.io/
[cct]: https://github.com/quangis/cct
[tools]: https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl
[tools2]: https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl
