quangis
===============================================================================

This repository contains implementations for the module components of the 
[QuAnGIS](https://questionbasedanalysis.com/) project. What follows is a brief 
description of the components, as well as a user's guide.



Usage
-------------------------------------------------------------------------------

For running specific components, refer to the corresponding section. To run 
tests:

    python3 -m unittest discover -s tests



Components
-------------------------------------------------------------------------------

### Query formulator

Online interface presenting users with a constrained natural language. Outputs 
a parse tree. The natural language parser is written in 
[ANTLR](https://www.antlr.org/). 

*To be implemented.*



### Query translator

Translates the parse tree into a *transformation algebra query*. A query is a 
directed acyclic graph for a (partial) workflow, with at least the requested 
workflow output CCD type as root. Hints on operations (e.g. CCT algebra 
transformations) are edges (to be matched to a workflow graph from the 
*workflow repository* via the *query executor*). The leaf nodes can have 
keywords (to be matched with possible inputs from the *data repository* via 
the *data reifier*). The CCT grammar is written in 
[ANTLR](https://www.antlr.org/). 

*To be implemented.*



### Query executor

Matches a query to a workflow, perhaps with graph matching algorithms or with 
SPARQL on the RDF graphs that encode the algebra expressions. For searching 
through the workflow repository, we use 
[MarkLogic](https://www.marklogic.com/).

*To be implemented.*



### Workflow specifier

Finds meaningful combinations of input/output CCD types for the transformation 
algebra query at hand. How?

*To be implemented.*



### Workflow generator

All possible workflows (without concrete datatypes) are pre-generated with 
[APE](https://github.com/sanctuuary/APE) every time a new *tool annotation* is 
added. Tool annotations contain CCD types for the input and output, as well as 
a description of the functionality by means of a CCT algebra expression in 
which those input/output types occur as variables.

The program takes as input the [CCD 
ontology](https://github.com/simonscheider/QuAnGIS/tree/master/Ontology/CoreConceptData.ttl) 
and [annotated 
tools](https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl). 
It translates them to a format APE understands and then runs APE on them.

Example run:

    python3 -m quangis.wfsyn \
        --tools ToolDescription.rdf \
        --types CoreConceptData.rdf

Make sure that `APE-1.1.5-executable.jar` exists in the `lib/` directory; it 
can be downloaded 
[here](https://github.com/sanctuuary/APE/releases/download/v1.1.5/APE-1.1.5-executable.jar). 
Suitable CCD ontology and tool annotation files will be downloaded 
automatically if they are not provided on the command line.



### Algebra abstractor

A CCT algebra expression is created for each workflow. This abstracts away 
over the specific tool annotations, into *types of transformations* in the CCT 
algebra. The algebra parser can be found 
[here](https://github.com/simonscheider/QuAnGIS/tree/master/TransformationAlgebra/AlgebraParsers).

*To be implemented.*



### Data reifier

Find suitable input data sources to concretize the queried workflow. Data 
sources are manually or automatically annotated with *CCD types* and *text 
annotations*. For searching through the data repository, we use 
[MarkLogic](https://www.marklogic.com/).

*To be implemented.*



More information
-------------------------------------------------------------------------------

-   [APE](https://ape-framework.readthedocs.io/) documentation, for the core 
    of the workflow synthesis.
-   [Jpype](https://jpype.readthedocs.io/) documentation, for the Python-Java 
    interface.
