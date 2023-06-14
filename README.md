# QuAnGIS workflows

This program is part of the [QuAnGIS][quangis] project.

-   It can **synthesize** GIS **workflows** from a specification of GIS 
    tools, using the [Automated Pipeline Explorer][ape].
-   It can also extract abstract specifications GIS **tools** from 
    manually constructed workflows, provided they are properly 
    [annotated][annot].
-   It also contains files related to the core concept transformation 
    algebra:
    -   The types and operators of the CCT transformation algebra are 
        defined in the [cct](cct/language.py) module.
    -   Descriptions of GIS tools in terms of expressions of the CCT algebra 
        can be found in [tools/tools.ttl](tools/tools.ttl).
    -   The [workflows/](workflows/) directory contains encodings of 
        workflows that make use of these tools.
    -   Encodings of the underlying tasks can be found in the 
        [tasks/](tasks/) directory.

Recipes to produce the files of this project are defined using 
[doit](https://pydoit.org/) in the [`dodo.py`](dodo.py) file. Run `doit 
list` to see an overview of what you can create.

## Installation

You will need Python 3.9. The tools are based on the 
[transforge](https://github.com/quangis/transforge) package developed 
for this project, which you will need to have installed.

    pip3 install 'transforge>=0.2.0'

During development, you likely want to install editable development 
versions:

    git clone --branch develop https://github.com/quangis/transforge
    pip3 install --editable transforge/

To generate workflows, Java 1.8+ must be installed. The correct version 
of APE and other required data files will automatically be downloaded. 
To run (rather limited) tests, install and run `nose2`.


## Workflow extraction

Assuming that RDF files containing manually annotated workflows are in 
the `ttl/` directory, the tool repository is built using:

    doit update_tools


## Workflow generation

There are two steps to the process: assembling a pipeline of tools, and 
annotating the conceptual steps they perform.

For the first step, datatypes and implementations are relevant. 
Therefore, the inputs and outputs of each tool in the 
[specification][tools] are annotated with core concept datatypes 
according to the [CCD][ccd] ontology. This is translated to a format 
that APE understands. APE is then instructed to generate workflows for 
different possible input/output data configurations. To perform this 
step, run:

    doit generate

The second step involves abstracting away from implementation details. 
For this, the tools are also annotated with a description of their 
functionality by means of a [CCT][cct] expression. This information is 
weaved into a graph of conceptual transformations via the 
[`transforge`][tf] library. To perform this step, run the following on 
the generated workflows:

    transforge graph -L cct -T build/tools.ttl \
        --skip-error build/solution-*.ttl

Finally, to query tasks like those 
[here](https://github.com/quangis/cct/tree/master/tasks):

    transforge query -L cct tasks/*.ttl


## Core concept transformation algebra

### Running

The `transforge` module can be used as a command-line interface to 
manipulate data produced with the CCT algebra. You can also use it to 
get visualizations and diagnostics information. Run `transforge --help` 
for a full overview of its capabilities.

-   The `graph` subcommand can use the CCT expressions of the 
    [tools](tools/tools.ttl) to turn [workflow](workflows/) graphs into 
    transformation graphs, and write them to a file or upload them to a 
    graph store. For example:
    ```
    transforge graph cct --tools=tools/tools.ttl \
        workflows/*.ttl -o output.trig
    ```

-   The `query` subcommand can turn [task](tasks/) descriptions into 
    SPARQL queries and fire them at a SPARQL endpoint. This will produce 
    CSV files that show which workflows are retrieved for which task 
    descriptions. For example:
    ```
    transforge query cct --server fuseki@https://localhost:3030/cct \
        tasks/*.ttl -o output.csv
    ```


### Tests

To reproduce our evaluations, set up a triple store like MarkLogic or Fuseki, 
change the `STORE_*` variables to the appropriate values and run `evaluate.py`. 
In the `build/` directory, tables will be produced for all evaluation variants 
used in our paper. Be advised: the queries are very unoptimized at the moment 
and some results will take a very a long time to build. MarkLogic is the 
fastest.

To perform sanity checks, run `nose2`.



### Serving a SPARQL endpoint

`rdflib` is not powerful enough to handle the workflow store in-memory, 
so you will need an external triple store. For open-source options, see 
[BlazeGraph](https://blazegraph.com/) or [Apache 
Fuseki](https://jena.apache.org/) 
([Virtuoso](https://virtuoso.openlinksw.com/) seems to have an issue 
with property paths).

[annot]: https://github.com/quangis/QuAnGIS_workflow_annotation
[quangis]: https://questionbasedanalysis.com/
[ccd]: http://geographicknowledge.de/vocab/CoreConceptData.rdf
[jpype]: https://jpype.readthedocs.io/
[ape]: https://github.com/sanctuuary/APE
[aped]: https://ape-framework.readthedocs.io/
[cct]: https://github.com/quangis/cct
[tf]: https://github.com/quangis/transforge
[tools]: https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl
[tools2]: https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl
