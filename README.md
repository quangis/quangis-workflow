# Core concept transformation algebra

This repository contains files related to the core concept 
transformation algebra of the 
[QuAnGIS](https://questionbasedanalysis.com/) project.

-   The types and operators of the CCT transformation algebra are 
    defined in [cct/language.py](cct/language.py).
-   Descriptions of GIS tools in terms of expressions of the CCT algebra 
    can be found in [tools/tools.ttl](tools/tools.ttl).
-   The [workflows/](workflows/) directory contains encodings of 
    workflows that make use of these tools.
-   Encodings of the underlying tasks can be found in the 
    [tasks/](tasks/) directory.

The `contra.py` tool from the `transformation-algebra` package is used 
to manipulate this data. You can also use it to get visualizations and 
diagnostics information. Run `contra.py -h` for a full overview of its 
capabilities.

-   The `graph` subcommand can use the CCT expressions of the 
    [tools](tools/tools.ttl) to turn [workflow](workflows/) graphs into 
    transformation graphs. For example:
    ```
    contra.py graph --language=cct.py --tools=tools/tools.ttl \
        workflows/10a-MalariaCongo.ttl output.ttl
    ```

-   The `query` subcommand can turn [task](tasks/) descriptions into 
    SPARQL queries and fire them at a SPARQL endpoint. This will produce 
    CSV files that show which workflows are retrieved for which task 
    descriptions. For example:
    ```
    contra.py query --endpoint=https://localhost/graphs --language=cct.py \
        tasks/*.ttl -o output.csv
    ```

There is a [Makefile](Makefile) with recipes that automate the process, 
assuming you have a Fuseki installation (see below). Run `make graphs` 
to obtain PDF representations of transformation graphs for all 
workflows. Run `make evaluations` to obtain tables for the evaluation 
variants used in our paper. Be advised: the queries are very unoptimized 
at the moment and some results will take a very a long time to build.


## Tests

To run the tests, simply run `nose2`.


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
with property paths). The Makefile has a variable pointing to Apache 
Jena and Apache Fuseki binaries, so make sure it points to the correct 
place for your installation.
