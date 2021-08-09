"""
Utilities and namespaces.
"""

import rdflib  # type: ignore
from rdflib import Graph
from rdflib.tools.rdf2dot import rdf2dot
from typing import Union
import io

from transformation_algebra.rdf import TA
from cct import cct

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
    "cct": cct.namespace}


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


def dot(g: Graph) -> str:
    """
    Turn a graph into GraphViz dot syntax. You can pass the output to such
    programs as `xdot` to visualize the RDF graph.
    """
    # rdf2dot uses deprecated cgi.escape function; this hack solves that
    import cgi
    import html
    stream = io.StringIO()
    cgi.escape = html.escape  # type: ignore
    rdf2dot(g, stream)
    return stream.getvalue()


def ttl(g: Graph) -> str:
    """
    Turn a graph into ttl syntax.
    """
    return g.serialize(format='ttl', encoding='utf-8').decode()
