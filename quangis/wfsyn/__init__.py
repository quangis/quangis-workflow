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
from quangis.wfsyn.tool import tool_annotations_ape


def tools_taxonomy(tools: Ontology) -> Ontology:
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


def types_taxonomy(types: Ontology,
                   dimensions: List[URIRef]) -> Ontology:
    """
    This method takes some ontology and returns a core OWL taxonomy.
    """

    taxonomy = Ontology()

    # Only keep subclass nodes intersecting with exactly one dimension
    for (o, p, s) in itertools.chain(
            types.triples((None, RDFS.subClassOf, None)),
            types.triples((None, RDF.type, OWL.Class))
            ):
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing and \
                types.dimensionality(o, dimensions) == 1:
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
    taxonomy = tools_taxonomy(tools) + types_taxonomy(types, dimensions)

    logging.info("Compute projected classes...")
    projection = semtype.project(ontology=types, dimensions=dimensions)

    logging.info("Transform tool annotations...")
    tools_ape = tool_annotations_ape(tools, projection, dimensions)

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
