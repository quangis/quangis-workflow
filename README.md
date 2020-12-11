workflow_synthesis
===============================================================================

This is a wrapper around [APE](https://github.com/sanctuuary/APE) for workflow 
synthesis in the [QuAnGIS](https://questionbasedanalysis.com) project. 

All possible workflows (without concrete datatypes) are pre-generated with 
[APE](https://github.com/sanctuuary/APE) every time a new *tool annotation* is 
added. Tool annotations contain CCD types for the input and output, as well as 
a description of the functionality by means of a CCT algebra expression in 
which those input/output types occur as variables.

The program takes as input a [CCD 
ontology](https://github.com/simonscheider/QuAnGIS/tree/master/Ontology/CoreConceptData.ttl) 
and suitable [tool 
annotations](https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl). 
It translates them to a format APE understands.

Example run:

    wfsyn.py \
        --ape APE-executable-1.0.2.jar \
        --tools ToolDescription.rdf \
        --types CoreConceptData.rdf

A suitable APE executable, CCD ontology and tool annotation will be downloaded 
automatically if they are not provided on the command line.
