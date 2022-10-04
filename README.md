# quangis-workflow-generator

This repository contains the implementation for workflow generation in 
the [QuAnGIS](https://questionbasedanalysis.com/) project. The program 
synthesizes GIS workflows from a specification of GIS tools, using the 
[Automated Pipeline Explorer][ape].

## Overview

There are two steps to the process: assembling a pipeline of tools, and 
annotating the conceptual steps they perform.

For the first step, datatypes and implementations are relevant. 
Therefore, the inputs and outputs of each tool in the 
[specification][tools] are annotated with core concept datatypes 
according to the [CCD][ccd] ontology. This is translated to a format 
that APE understands. APE is then instructed to generate workflows for 
different possible input/output data configurations.

The second step involves abstracting away from implementation details. 
For this, the tools are also annotated with a description of their 
functionality by means of a [CCT][cct] expression. This information is 
weaved into a graph of conceptual transformations via the 
[`transformation-algebra`][ta] library.


## Usage

Java and Python must be installed. To generate workflows, run `python -m 
quangis_wfgen`. To run (rather limited) tests, run `nose2`.


[ccd]: http://geographicknowledge.de/vocab/CoreConceptData.rdf
[jpype]: https://jpype.readthedocs.io/
[ape]: https://github.com/sanctuuary/APE
[aped]: https://ape-framework.readthedocs.io/
[cct]: https://github.com/quangis/cct
[ta]: https://github.com/quangis/transformation-algebra
[tools]: https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl
[tools2]: https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl
