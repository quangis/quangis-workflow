# Core concept transformation algebra

This repository contains files related to the core concept 
transformation algebra of the 
[QuAnGIS](https://questionbasedanalysis.com/) project.

-   The types and operators of the CCT transformation algebra are 
    defined in the [cct](cct/language.py) module.
-   Descriptions of GIS tools in terms of expressions of the CCT algebra 
    can be found in [tools/tools.ttl](tools/tools.ttl).
-   The [workflows/](workflows/) directory contains encodings of 
    workflows that make use of these tools.
-   Encodings of the underlying tasks can be found in the 
    [tasks/](tasks/) directory.

The `transforge` module can also be used as a command-line interface to 
manipulate this data. You can also use it to get visualizations and 
diagnostics information. Run `transforge --help` for a full overview of 
its capabilities.

-   The `graph` subcommand can use the CCT expressions of the 
    [tools](tools/tools.ttl) to turn [workflow](workflows/) graphs into 
    transformation graphs, and write them to a file or upload them to a 
    graph store. For example:
    ```
    transforge graph \
        --language=cct --tools=tools/tools.ttl \
        workflows/*.ttl -o output.trig
    ```

-   The `query` subcommand can turn [task](tasks/) descriptions into 
    SPARQL queries and fire them at a SPARQL endpoint. This will produce 
    CSV files that show which workflows are retrieved for which task 
    descriptions. For example:
    ```
    transforge query --language=cct \
        --backend fuseki --server https://localhost:3030/cct \
        tasks/*.ttl -o output.csv
    ```


## Tests

To reproduce our evaluations, set up a triple store like MarkLogic or Fuseki, 
change the `STORE_*` variables to the appropriate values and run `evaluate.py`. 
In the `build/` directory, tables will be produced for all evaluation variants 
used in our paper. Be advised: the queries are very unoptimized at the moment 
and some results will take a very a long time to build. MarkLogic is the 
fastest.

To perform sanity checks, run `nose2`.


## Installation

It is based on the [transforge](https://github.com/quangis/transforge) 
package developed for this project, which you will need to have 
installed.

    pip3 install 'transforge>=0.2.0'

## Development

During development, you likely want to install editable development 
versions of the two modules:

    git clone --branch develop https://github.com/quangis/transforge
    git clone https://github.com/quangis/cct
    pip3 install --editable transforge/
    pip3 install --editable cct/


## Serving a SPARQL endpoint

`rdflib` is not powerful enough to handle the workflow store in-memory, 
so you will need an external triple store. For open-source options, see 
[BlazeGraph](https://blazegraph.com/) or [Apache 
Fuseki](https://jena.apache.org/) 
([Virtuoso](https://virtuoso.openlinksw.com/) seems to have an issue 
with property paths).
