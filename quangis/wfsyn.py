"""
Workflow synthesis.
"""

import logging
from rdflib import URIRef
from typing import List, Tuple, Iterable

import ape
import semtype
import ontology
from semtype import SemType
from namespace import CCD, TOOLS
from ontology import Ontology, Taxonomy
from ontology.tool import ontology_to_json, ToolsJSON


def wfsyn(types: Ontology,
          tools: Ontology,
          solutions: int,
          dimensions: List[URIRef],
          io: List[Tuple[List[SemType], List[SemType]]]) \
          -> Iterable[List[ape.Workflow]]:

    logging.info("Compute taxonomies...")
    types_tax = ontology.clean_owl_ontology(types, dimensions)
    tools_tax = ontology.extract_tool_ontology(tools)

    logging.info("Compute projected classes...")
    projection = semtype.project(taxonomy=types_tax, dimensions=dimensions)

    logging.info("Combine taxonomies...")
    taxonomy = tools_tax + types_tax.core(dimensions)

    logging.info("Transform tool annotations...")
    tools_ape = ontology_to_json(tools, projection, dimensions)

    logging.info("Running APE...")
    jvm = ape.APE(
        taxonomy=taxonomy,
        tools=tools_ape,
        tool_root=TOOLS.Tool,
        namespace=CCD,
        dimensions=dimensions)

    for i, o in io:
        yield jvm.run(
            inputs=i,
            outputs=o,
            solutions=solutions)
