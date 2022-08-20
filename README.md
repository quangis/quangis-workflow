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

The `transformation-algebra` module can also be used as a command-line 
interface to manipulate this data. You can also use it to get 
visualizations and diagnostics information. Run `python -m 
transformation_algebra --help` for a full overview of its capabilities.

-   The `graph` subcommand can use the CCT expressions of the 
    [tools](tools/tools.ttl) to turn [workflow](workflows/) graphs into 
    transformation graphs, and write them to a file or upload them to a 
    graph store. For example:
    ```
    python -m transformation_algebra graph \
        --language=cct --tools=tools/tools.ttl \
        workflows/*.ttl -o output.trig
    ```

-   The `query` subcommand can turn [task](tasks/) descriptions into 
    SPARQL queries and fire them at a SPARQL endpoint. This will produce 
    CSV files that show which workflows are retrieved for which task 
    descriptions. For example:
    ```
    python -m transformation_algebra query --language=cct \
        --backend fuseki --server https://localhost:3030/cct \
        tasks/*.ttl -o output.csv
    ```


## Tests

To reproduce our evaluations, run `evaluate.py`. In the `build/` 
directory, tables will be produced for all evaluation variants used in 
our paper. You will also need Java, since the Apache Jena Fuseki triple 
store will be automatically downloaded and run. Be advised: the queries 
are very unoptimized at the moment and some results will take a very a 
long time to build.

To perform sanity checks, run `nose2`.


## Installation

It is based on the 
[transformation-algebra](https://github.com/quangis/transformation-algebra) 
package developed for this project, which you will need to have 
installed.

    pip3 install 'transformation-algebra>=0.2.0'

Since v0.2 is not yet released as of the time of writing, you will 
probably need to install the development branch of the library.


## Development

During development, you likely want to install editable versions of the 
two modules:

    git clone --branch develop https://github.com/quangis/transformation-algebra
    git clone https://github.com/quangis/cct
    pip3 install --editable transformation-algebra/
    pip3 install --editable cct/


## Serving a SPARQL endpoint

`rdflib` is not powerful enough to handle the workflow store in-memory, 
so you will need an external triple store. For open-source options, see 
[BlazeGraph](https://blazegraph.com/) or [Apache 
Fuseki](https://jena.apache.org/) 
([Virtuoso](https://virtuoso.openlinksw.com/) seems to have an issue 
with property paths).
