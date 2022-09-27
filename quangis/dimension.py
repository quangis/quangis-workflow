"""
Methods and datatypes to manipulate taxonomies.
"""

from __future__ import annotations

from rdflib.term import Node
from quangis.namespace import RDFS
from rdflib import Graph


class Dimension(Graph):
    """
    A semantic dimension is a directed acyclic graph of semantic subclasses
    belonging to that dimension.
    """

    def __init__(self, root: Node, source: Graph):
        super().__init__()
        self.root = root

        def f(node):
            for child in source.subjects(RDFS.subClassOf, node):
                # TODO catch cycles
                self.add((child, RDFS.subClassOf, node))
                f(child)

        f(root)

    def parents(self, node: Node) -> list[Node]:
        return list(self.objects(node, RDFS.subClassOf))
