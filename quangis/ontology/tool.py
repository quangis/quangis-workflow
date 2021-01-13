"""
This module contains functions to work with tool annotations.
"""

from rdflib import URIRef, BNode
from typing import Mapping, List, Dict
from typing_extensions import TypedDict

from quangis.namespace import TOOLS, WF, RDF
from quangis.ontology import Ontology
from quangis.semtype import SemType
from quangis.utils import shorten

ToolJSON = TypedDict('ToolJSON', {
    'id': str,
    'label': str,
    'inputs': List[Dict[URIRef, List[URIRef]]],
    'outputs': List[Dict[URIRef, List[URIRef]]],
    'taxonomyOperations': List[URIRef]
})

ToolsJSON = TypedDict('ToolsJSON', {
    'functions': List[ToolJSON]
})


def get_resources(
        ontology: Ontology,
        tool: URIRef,
        *predicates: List[URIRef]) -> List[BNode]:
    """
    Get the resources input/output associated with a tool, with predicates like
    output1/input2... etcetera.
    """
    resources = []
    for p in predicates:
        resource = ontology.value(predicate=p, subject=tool, any=False)
        if resource:
            resources.append(resource)
    return resources


def get_type(
        ontology: Ontology,
        resource: BNode,
        projection: Mapping[URIRef, SemType],
        dimensions: List[URIRef]) -> SemType:
    """
    Returns a list of types of some tool input/output which are all projected
    to given semantic dimension
    """

    # Construct the type of this resource node
    result = SemType()
    for d in dimensions:
        types = []
        for t in ontology.objects(resource, RDF.type):
            if t in projection and projection[t][d]:
                types.extend(projection[t][d])
        # If there is no type, just use the highest type of the corresponding
        # dimension
        result[d].extend(types or [d])
    return result


def ontology_to_json(
        tools: Ontology,
        projection: Mapping[URIRef, SemType],
        dimensions: List[URIRef]) -> ToolsJSON:
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
                    get_type(tools, resource, projection, dimensions).mapping
                    for resource in get_resources(
                        tools, tool, WF.input1, WF.input2, WF.input3)
                ],
                'outputs': [
                    o for o in (
                        get_type(tools, resource, projection, dimensions).downcast().mapping
                        for resource in get_resources(
                            tools, tool, WF.output, WF.output2, WF.output3)
                    ) if o is not None]
            }
            for tool in tools.objects(None, TOOLS.implements)
        ]
    }
