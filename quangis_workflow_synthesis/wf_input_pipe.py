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

from rdfnamespaces import CCD
import wf_taxonomy_cleaner
import tool_annotator
import semdim_projector

import rdflib
import os


def rdf(path, format="turtle"):
    """
    Load an RDF graph from a file.
    """
    g = rdflib.Graph()
    g.parse(path, format="turtle")
    return g


def main():

    ont_types = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/Ontology/CoreConceptData.ttl")
    ont_tools = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription.ttl")
    tooldesc_flgraph = rdf("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription_flgraph.ttl")

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    tax_types = wf_taxonomy_cleaner.cleanOWLOntology(ont_types)
    tax_tools = wf_taxonomy_cleaner.extractToolOntology(ont_tools)

    # For comparison with old output
    tax_types.serialize(destination="build/CoreConceptData_tax.ttl", format="turtle")
    tax_tools.serialize(destination="build/FlowmapDescription_tax.ttl", format="turtle")

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file. Generates a file
    # 'CoreConceptData_tax_core.ttl' which contains the ontology cleaned from
    # non-core nodes (=not belonging to the core of a dimension)

    # dimnodes = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
    # dimnodes_fl = [CCD.DType]
    dimnodes_flgraph = [CCD.CoreConceptQ, CCD.LayerA]
    (tax_types_core_fl, project) = semdim_projector.main(taxonomy=tax_types, dimnodes=dimnodes_flgraph)

    # For comparison with old output
    tax_types_core_fl.serialize(destination="build/CoreConceptData_tax_core_flgraph.ttl", format="turtle")

    # Combine tool & type taxonomies
    final = rdflib.Graph()
    final += tax_tools
    final += tax_types_core_fl
    final.serialize(destination="build/GISTaxonomy_flgraph.rdf", format="application/rdf+xml")

    # Generate JSON version of the tool annotations with the projected classes,
    # to be used as APE input with the full taxonomy
    tool_annotator.main(tooldesc_flgraph,
                        project,
                        dimnodes_flgraph,
                        mainprefix=CCD,
                        targetpath="build/FlowmapDescription_flgraph.json")


if __name__ == '__main__':
    main()
