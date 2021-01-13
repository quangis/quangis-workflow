"""
This module contains functions to work with tool annotations.
"""

from ontology import Ontology
from namespace import TOOLS, WF, CCD, shorten
from semantic_dimensions import SemTypeDict, SemType


from rdflib import Graph, URIRef, Namespace, BNode
from rdflib.term import Node
from rdflib.namespace import RDF
from typing import Mapping, List, Dict, NewType
from typing_extensions import TypedDict

# from six.moves.urllib.parse import urldefrag
# 
# def frag(node):
#     return urldefrag(node).fragment


import logging

ToolJSON = TypedDict('ToolJSON', {
    'id': str,
    'label': str,
    'inputs': List[SemTypeDict],
    'outputs': List[SemTypeDict],
    'taxonomyOperations': List[URIRef]
})

ToolsJSON = TypedDict('ToolsJSON', {
    'functions': List[ToolJSON]
})


def downcast(node: URIRef) -> URIRef:
    """
    Downcast certain nodes to identifiable leaf nodes. APE has a closed world
    assumption, in that it considers the set of leaf nodes it knows about as
    exhaustive: it will never consider branch nodes as valid answers.
    """
    return {
        CCD.NominalA: CCD.PlainNominalA,
        CCD.OrdinalA: CCD.PlainOrdinalA,
        CCD.IntervalA: CCD.PlainIntervalA,
        CCD.RatioA: CCD.PlainRatioA
    }.get(node, node)


def getinoutypes(
        g,
        tool_resource_node: BNode,
        projection: Mapping[Node, SemType],
        dimension: URIRef) -> List[URIRef]:
    """
    Returns a list of types of some tool input/output which are all projected
    to given semantic dimension
    """

    types = []
    for t in g.objects(tool_resource_node, RDF.type):
        if t in projection and projection[t][dimension]:
            types.extend(projection[t][dimension])

    # In case there is no type, just use the highest level type of the
    # corresponding dimension
    return types or [dimension]


def ontology_to_json(
        tools: Ontology,
        projection: Mapping[Node, SemType],
        dimensions: List[URIRef]) -> ToolsJSON:
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    result: List[ToolJSON] = []

    for tool in tools.objects(None, TOOLS.implements):

        inputs = []
        for input_pred in (WF.input1, WF.input2, WF.input3):
            node = tools.value(predicate=input_pred, subject=tool, any=False)
            if node:
                inputs.append({
                    d: getinoutypes(tools, node, projection, d)
                    for d in dimensions
                })

        outputs = []
        for output_pred in (WF.output, WF.output2, WF.output3):
            node = tools.value(predicate=output_pred, subject=tool, any=False)
            if node:
                # Tool outputs should always be downcast
                outputs.append({
                    d: [downcast(c) for c in getinoutypes(tools, node, projection, d)]
                    for d in dimensions
                })

        result.append({
            'id': str(tool),
            'label': shorten(tool),
            'inputs': inputs,
            'outputs': outputs,
            'taxonomyOperations': [tool]
        })
    return ToolsJSON({"functions": result})
