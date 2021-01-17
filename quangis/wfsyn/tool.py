"""
This module contains functions to work with tool annotations.
"""

from rdflib import URIRef, BNode
from typing import Mapping, List, Dict
from typing_extensions import TypedDict

from quangis.namespace import TOOLS, WF, RDF
from quangis.ontology import Ontology
from quangis.semtype import SemType
from quangis.util import shorten

ToolDict = TypedDict('ToolDict', {
    'id': str,
    'label': str,
    'inputs': List[Dict[URIRef, List[URIRef]]],
    'outputs': List[Dict[URIRef, List[URIRef]]],
    'taxonomyOperations': List[URIRef]
})

ToolsDict = TypedDict('ToolsDict', {
    'functions': List[ToolDict]
})


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


def get_type(
        tools: Ontology,
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
        for t in tools.objects(resource, RDF.type):
            if t in projection and projection[t][d]:
                types.extend(projection[t][d])
        # If there is no type, just use the highest type of the corresponding
        # dimension
        result[d].extend(types or [d])
    return result


def tool_annotations_ape(
        tools: Ontology,
        projection: Mapping[URIRef, SemType],
        dimensions: List[URIRef]) -> ToolsDict:
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
                    get_type(
                        tools, resource, projection, dimensions
                    ).as_dictionary()
                    for resource in get_resources(tools, tool, is_output=False)
                ],
                'outputs': [
                    get_type(
                        tools, resource, projection, dimensions
                    ).downcast().as_dictionary()
                    for resource in get_resources(tools, tool, is_output=True)
                ]
            }
            for tool in tools.objects(predicate=TOOLS.implements)
        ]
    }

