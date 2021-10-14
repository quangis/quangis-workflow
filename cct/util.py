"""
Utilities and namespaces.
"""

import rdflib  # type: ignore
from rdflib import Graph
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from typing import Union

from transformation_algebra.rdf import TA
from cct.cct import CCT

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
GIS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
WF = rdflib.Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")

namespaces = {
    "rdf": RDF,
    "rdfs": RDFS,
    "wf": WF,
    "tools": TOOLS,
    "ta": TA,
    "cct": CCT}


def graph(*gs: Union[str, Graph]) -> Graph:
    """
    Merge graphs from a file or other graphs.
    """
    graph = Graph()
    for g in gs:
        if isinstance(g, str):
            graph.parse(g, format=rdflib.util.guess_format(g))
        else:
            assert isinstance(g, Graph)
            graph += g
    return graph


def write_dot(g: Graph, fn: str, directory="build/") -> None:
    """
    Turn a graph into GraphViz dot syntax. You can pass the output to such
    programs as `xdot` to visualize the RDF graph.
    """
    with open(fn + ".dot", 'w') as f:
        rdf2dot(g, f)


def write_ttl(g: Graph, fn: str, directory="build/") -> None:
    """
    Turn a graph into ttl syntax.
    """
    g.serialize(format="ttl", destination=fn + ".ttl", encoding='utf-8')
