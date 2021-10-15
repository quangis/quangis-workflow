"""
Utilities and namespaces.
"""

import os
import os.path
import rdflib  # type: ignore
import itertools
from rdflib import Graph
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from transformation_algebra.rdf import TA
from collections import defaultdict
from typing import Union

from cct import CCT

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


def write_graph(g: Graph, name: str, path="build/") -> None:
    """
    Output a graph in Turtle format and a visualization in GraphViz dot syntax.
    """
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, name + ".dot"), 'w') as f:
        rdf2dot(g, f)

    g.serialize(format="ttl", destination=os.path.join(path, name + ".ttl"),
        encoding='utf-8')


def write_text(name, string, path="build/") -> None:
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, name), 'w') as f:
        f.write(string)


class Labeller(defaultdict):
    """
    A labeller assigns a fresh name to anything it accesses.
    """

    def __init__(self, f=lambda x: x):
        self.enumerator = itertools.count(start=1)
        super().__init__(lambda: f(next(self.enumerator)))
