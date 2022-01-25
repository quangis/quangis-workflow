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


## Usage

The types and operators of the CCT transformation algebra are defined in 
[cct.py](cct.py). Descriptions of GIS tools in terms of expressions of the CCT 
algebra are contained in [tools/tools.ttl](tools/tools.ttl).


#### Generating transformation graphs

[utils/generate_graphs.py](utils/generate_graphs.py) generates `.ttl` files 
that represent the transformation graphs for the workflows as they are 
described in [scenarios/](scenarios), which are in turn described in terms of 
the GIS tools of [tools.ttl](tools/tools.ttl).


#### Serving a SPARQL endpoint

`rdflib` is not powerful enough to handle the workflow store in-memory, so you 
will need an external triple store. For open-source options, see 
[BlazeGraph](https://blazegraph.com/) or [Apache 
Jena](https://jena.apache.org/) ([Virtuoso](https://virtuoso.openlinksw.com/) 
seems to have an issue with property paths).

The script at [utils/serve_sparql_endpoint.sh](utils/serve_sparql_endpoint.sh) 
downloads and runs Apache Jena on the generated `.ttl` files.


#### Firing queries

The script at [utils/run_queries.py](utils/run_queries.py) fires the queries 
defined in the [queries/](queries/) directory at the SPARQL endpoint.


#### Workflow analysis

To analyze what the expressions and transformation graphs actually look like, 
use [utils/analyze_workflows.py](utils/analyze_workflows.py). This script 
generates simplified graphs and a text description of the tools used in each 
workflow.
