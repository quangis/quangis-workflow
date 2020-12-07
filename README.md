quangis-workflow-synthesis
===============================================================================

This is a wrapper around [APE](https://github.com/sanctuuary/APE). 

All possible workflows (without concrete datatypes) are pre-generated with 
[APE](https://github.com/sanctuuary/APE) every time a new *tool annotation* is 
added. Tool annotations contain CCD types for the input and output, as well as 
a description of the functionality by means of a CCT algebra expression in 
which those input/output types occur as variables.

APE needs the [CCD 
ontology](https://github.com/simonscheider/QuAnGIS/tree/master/Ontology/CoreConceptData.ttl) 
and the [tool 
annotations](https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl).
