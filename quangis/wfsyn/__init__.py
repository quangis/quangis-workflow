"""
Workflow synthesis.
"""

import logging
from rdflib import URIRef
from typing import List, Tuple, Iterable

from quangis import semtype
from quangis import ontology
from quangis.semtype import SemType
from quangis.namespace import CCD, TOOLS
from quangis.ontology import Ontology
from quangis.wfsyn import ape
from quangis.wfsyn.tool import ontology_to_json


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
    projection = semtype.project(ontology=types_tax, dimensions=dimensions)

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
