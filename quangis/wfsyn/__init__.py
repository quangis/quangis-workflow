"""
Workflow synthesis.
"""

import logging
import itertools
from rdflib import URIRef, BNode
from typing import List, Tuple, Iterable

from quangis.semtype import SemType
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA, WF
from quangis.ontology import Ontology
from quangis.taxonomy import Taxonomy
from quangis.util import shorten
from quangis.wfsyn import ape


def get_resources(
        tools: Ontology,
        tool: URIRef,
        is_output: bool) -> List[BNode]:
    """
    Get the input/output resource nodes associated with a tool.
    """
    if is_output:
        predicates = (WF.output, WF.output2, WF.output3)
    else:
        predicates = (WF.input1, WF.input2, WF.input3)

    resources = []
    for p in predicates:
        resource = tools.value(predicate=p, subject=tool, any=False)
        if resource:
            resources.append(resource)
    return resources


def get_types(tools: Ontology, resource: BNode) -> List[URIRef]:
    """
    Returns a list of types of some tool input/output resource.
    """
    return list(tools.objects(resource, RDF.type))


def tool_annotations_ape(
        tools: Ontology, dimensions: List[Taxonomy]) -> ape.ToolsDict:
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    return {
        'functions': [
            {
                'id': str(tool),
                'label': shorten(tool),
                'taxonomyOperations': [tool],
                'inputs': [
                    SemType.project(
                        dimensions, get_types(tools, resource)
                    ).to_dict()
                    for resource in get_resources(tools, tool, is_output=False)
                ],
                'outputs': [
                    SemType.project(
                        dimensions, get_types(tools, resource)
                    ).downcast().to_dict()
                    for resource in get_resources(tools, tool, is_output=True)
                ]
            }
            for tool in tools.objects(predicate=TOOLS.implements)
        ]
    }


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

    logging.info("Compute subsumption trees...")
    dimension_trees = [
        Taxonomy.from_ontology(types, dimension)
        for dimension in dimensions
    ]

    logging.info("Create taxonomies for APE...")
    taxonomy = tools_taxonomy(tools)
    taxonomy += types_taxonomy(types, dimensions)

    logging.info("Create tool annotations for APE...")
    tools_ape = tool_annotations_ape(tools, dimension_trees)

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
