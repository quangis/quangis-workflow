"""
This module contains functions to work with tool annotations.
"""

from rdflib import URIRef, BNode
from typing import List, Dict
from typing_extensions import TypedDict

from quangis.namespace import TOOLS, WF, RDF
from quangis.ontology import Ontology, Taxonomy
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


def get_types(tools: Ontology, resource: BNode) -> List[URIRef]:
    """
    Returns a list of types of some tool input/output resource.
    """
    return list(tools.objects(resource, RDF.type))


def tool_annotations_ape(
        tools: Ontology, dimensions: List[Taxonomy]) -> ToolsDict:
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

