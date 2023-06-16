# QuAnGIS workflows

This repository is part of the [QuAnGIS][quangis] project. It 
encompasses the definition of the **core concept transformation 
algebra**, and a database of **GIS tools** specified in terms of it. It 
also contains recipes to produce and transform **workflows** using these 
tools.

The recipes are specified using [doit](https://pydoit.org/) in the 
[`dodo.py`](dodo.py) file. Run `doit list` to see an overview of what 
you can create.


## Installation

You will need Python 3.9 as well as the dependencies specified in 
[`requirements.txt`](requirements.txt). To generate workflows, Java 1.8+ 
must be installed; a version of APE will automatically be downloaded.


## Workflow abstraction and tool database

We distinguish two types of workflow specification: *concrete* and 
*abstract*. *Concrete* workflows consist of concrete tools, as 
implemented in ArcGIS or QGIS. *Abstract* workflows consist of abstract 
tools that may be implemented by one or more concrete tools (which may, 
in turn, implement multiple abstract tools). Only abstract workflows can 
be annotated with CCT expressions (see below).

For now, the [annotation repository][annot] contains concrete workflows. 
There are abstract workflows in the directory 
[`data/workflows/`](`data/workflows/`), which were used for our initial 
evaluations. Abstract workflows can also be generated (see below).

Abstract and concrete GIS tools are described in the tool database at 
[`data/tools/`](data/tools/). Furthermore, new abstract tools can be 
*extracted* from properly annotated concrete workflows. Assuming that 
concrete workflows in `.ttl` format have been put in the 
[`data/workflows-concrete/`] directory, you can do this via:

    doit update_tools

Assuming that the tool database is up-to-date, the concrete workflow can 
then be converted into abstract workflows:

    doit abstract


## Workflow synthesis

Abstract workflows can be **synthesized** from the abstract tool 
specifications sing the [Automated Pipeline Explorer][ape].

To assemble a pipeline of tools, datatypes and implementations are 
relevant. Therefore, the inputs and outputs of each abstract tool in the 
tool database are annotated with core concept datatypes according to the 
[CCD][ccd] ontology. This is translated to a format that APE 
understands. APE is then instructed to generate workflows for different 
possible input/output data configurations, as specified in 
[`data/ioconfig.ttl`](data/ioconfig.ttl). To perform this step, run:

    doit generate


## Core concept transformations

Workflows can be annotated with the conceptual steps they perform. This 
abstracts away from implementation details. For this, the abstract tools 
are also annotated with a description of their functionality by means of 
a CCT expression. The types and operators of the CCT transformation 
algebra are defined in the [`quangis/cct.py`](quangis/cct.py) module.

This information is then weaved into a graph of conceptual 
transformations via the [`transforge`][tf] library, which was developed 
for this purpose. To perform this step on the manual abstract workflows 
of [`data/workflows/`](data/workflows/), run the following:

    doit transformations_ttl

Or, for a visual representation:

    doit transformations_pdf


## Evaluation

The [`data/workflows/`](data/workflows/) directory contains workflows 
that answer particular questions. These questions, in turn, correspond 
to tasks that are encoded as transformation graphs in the 
[`data/tasks/`](data/tasks/) directory.

These can then be turned into SPARQL queries and fired at a SPARQL 
endpoint. `rdflib` is not powerful enough to handle the workflow store 
in-memory, so you will need an external triple store. For open-source 
options, see [BlazeGraph](https://blazegraph.com/) or [Apache 
Fuseki](https://jena.apache.org/) 
([Virtuoso](https://virtuoso.openlinksw.com/) seems to have an issue 
with property paths). We currently use the proprietary 
[MarkLogic](https://marklogic.com).

This is the basis of our evaluations. To reproduce our them, set up a 
triple store like MarkLogic, change the `STORE_*` variables to the 
appropriate values and run:

    doit evaluate

In the `build/eval/` directory, CSV files will be produced that show 
which workflows are retrieved for which task descriptions, for all 
evaluation variants used in our paper. Be advised: the queries are very 
unoptimized at the moment and some results will take a very a long time 
to build. MarkLogic is the fastest.


### Tests

To run (rather limited) tests, and sanity checks, install and run 
`nose2`.


[annot]: https://github.com/quangis/QuAnGIS_workflow_annotation
[quangis]: https://questionbasedanalysis.com/
[ccd]: http://geographicknowledge.de/vocab/CoreConceptData.rdf
[jpype]: https://jpype.readthedocs.io/
[ape]: https://github.com/sanctuuary/APE
[aped]: https://ape-framework.readthedocs.io/
[cct]: https://github.com/quangis/cct
[tf]: https://github.com/quangis/transforge
