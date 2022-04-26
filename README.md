Core concept transformation algebra
===============================================================================

This repository contains the implementation for the core concept 
transformation algebra of the [QuAnGIS](https://questionbasedanalysis.com/) 
project.

It is based on the 
[transformation-algebra](https://github.com/quangis/transformation-algebra) 
package developed for this project, which you will need to have installed:

    pip3 install 'transformation-algebra>=0.2.0'

Since v0.2 is not yet released as of the time of writing, you will probably 
need to install the development branch of the library. To install an editable 
version of the library:

    git clone --branch develop https://github.com/quangis/transformation-algebra
    cd transformation-algebra
    pip3 install --editable .

You can then clone this repository and use it.


## Overview

-   The types and operators of the CCT transformation algebra are defined in 
    [cct.py](cct.py).
-   Descriptions of GIS tools in terms of expressions of the CCT algebra are 
    contained in [tools/tools.ttl](tools/tools.ttl).
-   The [workflows/](workflows/) directory contains encodings of workflows that 
    make use of those tools.
-   The underlying tasks can be found in the [tasks/](tasks/) directory.

The `ta-tool` is used to manipulate this data. You can also use it to get 
visualizations and diagnostics information. Run `ta-tool -h` for a full 
overview of its capabilities. It is now [here](utils/ta-tool.py) but should be 
integrated in the transformation-algebra library in the future.

-   The `ta-tool graph` subcommand uses the algebra expressions of the 
    [tools](tools/tools.ttl) to turn [workflow](workflows/) graphs into 
    transformation graphs.
-   The `ta-tool query` subcommand can turn [task](tasks/) descriptions into 
    SPARQL queries and fire them at a SPARQL endpoint. This will produce CSV 
    files that show which workflows are retrieved for which task descriptions.

There is a [Makefile](Makefile) with recipes that automate the process, 
assuming you have a Fuseki installation (see below). Run `make graphs` to 
obtain PDF representations of transformation graphs for all workflows. Run 
`make evaluations` to obtain tables for the evaluation variants used in our 
paper. Be advised: the queries are very unoptimized at the moment and some 
results will take a very a long time to build.


## Serving a SPARQL endpoint

`rdflib` is not powerful enough to handle the workflow store in-memory, so you 
will need an external triple store. For open-source options, see 
[BlazeGraph](https://blazegraph.com/) or [Apache 
Fuseki](https://jena.apache.org/) ([Virtuoso](https://virtuoso.openlinksw.com/) 
seems to have an issue with property paths). The Makefile has a variable 
pointing to Apache Jena and Apache Fuseki binaries, so make sure it points to 
the correct place for your installation.
