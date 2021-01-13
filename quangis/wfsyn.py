"""
Workflow synthesis.
"""

import logging
from rdflib import URIRef
from typing import List, Tuple

import semtype
import ontology
from ontology import Ontology, Taxonomy
from ontology.tool import ontology_to_json, ToolsJSON


def wfsyn(types: Ontology,
          tools: Ontology,
          dimensions: List[URIRef]) -> Tuple[Taxonomy, ToolsJSON]:

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    logging.info("Compute taxonomies...")
    types_tax = ontology.clean_owl_ontology(types, dimensions)
    tools_tax = ontology.extract_tool_ontology(tools)

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file
    logging.info("Compute projected classes...")
    projection = semtype.project(taxonomy=types_tax, dimensions=dimensions)

    # Combine tool & type taxonomies
    logging.info("Combine taxonomies...")
    taxonomies = tools_tax + types_tax.core(dimensions)

    # Transform tool annotations with the projected classes into APE input
    logging.info("Transform tool annotations...")
    tools_ape = ontology_to_json(tools, projection, dimensions)

    return taxonomies, tools_ape
