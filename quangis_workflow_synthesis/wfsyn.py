# -*- coding: utf-8 -*-
"""
Generates input data for workflow generator (APE) from a given OWL data
ontology and a given tool annotation file, by projecting classes to ontology
dimensions.

@author: Schei008
@date: 2020-04-08
@copyright: (c) Schei008 2020
@license: MIT
"""

from rdf_namespaces import CCD
import taxonomy
import semantic_dimensions
import ape_tools

import rdflib
import json


def rdf(path, format='turtle'):
    """
    Load an RDF graph from a file.
    """
    g = rdflib.Graph()
    g.parse(path, format=format)
    return g


def main(dimensions=semantic_dimensions.FLATGRAPH):

    types = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/Ontology/CoreConceptData.ttl")
    tools = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription.ttl")
    tooldesc_flgraph = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription_flgraph.ttl")

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    types_tax = taxonomy.cleanOWLOntology(types)
    tools_tax = taxonomy.extractToolOntology(tools)

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file, and clear the ontology
    # from non-core nodes
    types_tax_core_fl, projection = \
        semantic_dimensions.project(taxonomy=types_tax, dimnodes=dimensions)

    # Combine tool & type taxonomies
    final = tools_tax + types_tax_core_fl
    final.serialize(destination="build/GISTaxonomy_flgraph.rdf",
                    format="application/rdf+xml")

    # Transform tool annotations with the projected classes into APE input
    ape_input = ape_tools.rdf2ape(tooldesc_flgraph,
                                  projection,
                                  dimensions,
                                  mainprefix=CCD)

    with open("build/FlowmapDescription_flgraph.json", 'w') as f:
        json.dump(ape_input, f, sort_keys=True, indent=2)

    # For comparison with old output
    # tax_types.serialize(destination="build/CoreConceptData_tax.ttl", format="turtle")
    # tax_tools.serialize(destination="build/FlowmapDescription_tax.ttl", format="turtle")
    # tax_types_core_fl.serialize(destination="build/CoreConceptData_tax_core_flgraph.ttl", format="turtle")


if __name__ == '__main__':
    main()
