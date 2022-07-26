# quangis-workflow-synthesis

This repository contains the implementation for workflow synthesis in 
the [QuAnGIS](https://questionbasedanalysis.com/) project. What follows 
is a brief description of the components, as well as a user's guide.


# Usage

All possible workflows (without concrete datatypes) are pre-generated 
with [APE](https://github.com/sanctuuary/APE) when a new *tool 
annotation* is added. Tool annotations contain CCD types for the input 
and output, as well as a description of the functionality by means of a 
CCT algebra expression in which those input/output types occur as 
variables.

This program takes as input the [CCD 
ontology](https://github.com/simonscheider/QuAnGIS/tree/master/Ontology/CoreConceptData.ttl) 
and [annotated 
tools](https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl). 
It translates them to a format APE understands and then runs APE on 
them.

Example run:

    python3 -m quangis.wfsyn \
        --tools ToolDescription.rdf \
        --types CoreConceptData.rdf

Make sure that `APE-1.1.5-executable.jar` exists in the `lib/` 
directory; it can be downloaded 
[here](https://github.com/sanctuuary/APE/releases/download/v1.1.5/APE-1.1.5-executable.jar). 
Suitable CCD ontology and tool annotation files will be downloaded 
automatically if they are not provided on the command line.

To run tests, simply run `nose2`.


# More information

-   [APE](https://ape-framework.readthedocs.io/) documentation, for the core 
    of the workflow synthesis.
-   [Jpype](https://jpype.readthedocs.io/) documentation, for the Python-Java 
    interface.
