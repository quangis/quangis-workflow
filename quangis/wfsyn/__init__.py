"""
Workflow synthesis.
"""

import logging
import itertools
from rdflib import URIRef, BNode
from typing import List, Tuple, Iterable

from quangis import semtype
from quangis.semtype import SemType
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA
from quangis.ontology import Ontology
from quangis.wfsyn import ape
from quangis.wfsyn.tool import ontology_to_json


def extract_tool_ontology(tools: Ontology) -> Ontology:
    """
    Extracts a taxonomy of toolnames from the tool description.
    """

    taxonomy = Ontology()
    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        taxonomy.add((o, RDFS.subClassOf, s))
        taxonomy.add((s, RDF.type, OWL.Class))
        taxonomy.add((o, RDF.type, OWL.Class))
        taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))
    return taxonomy


def clean_owl_ontology(ontology: Ontology,
                       dimensions: List[URIRef]) -> Ontology:
    """
    This method takes some ontology and returns an OWL taxonomy.
    """

    taxonomy = Ontology()

    # Only keep subclass nodes intersecting with exactly one dimension
    for (o, p, s) in itertools.chain(
            ontology.triples((None, RDFS.subClassOf, None)),
            ontology.triples((None, RDF.type, OWL.Class))
            ):
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing and \
                ontology.dimensionality(o, dimensions) == 1:
            taxonomy.add((o, p, s))

    # Add common upper class for all data types
    taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

    return taxonomy


def wfsyn(types: Ontology,
          tools: Ontology,
          solutions: int,
          dimensions: List[URIRef],
          io: List[Tuple[List[SemType], List[SemType]]]) \
          -> Iterable[List[ape.Workflow]]:

    logging.info("Compute taxonomies...")
    types_tax = clean_owl_ontology(types, dimensions)
    tools_tax = extract_tool_ontology(tools)
    taxonomy = tools_tax + types_tax.core(dimensions)

    logging.info("Compute projected classes...")
    projection = semtype.project(ontology=types, dimensions=dimensions)

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
