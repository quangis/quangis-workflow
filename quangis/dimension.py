"""
Methods and datatypes to manipulate taxonomies.
"""

from __future__ import annotations

import logging
from rdflib.term import Node

from quangis import error
from quangis.namespace import RDFS
from quangis.util import shorten
from rdflib import Graph


class Dimension(object):
    """
    A semantic dimension is a directed acyclic graph of semantic subclasses
    belonging to that dimension.
    """

    def __init__(self, root: Node):
        self._root = root
        self._parents: dict[Node, Node] = {}
        self._depth: dict[Node, int] = {}

    def __str__(self, node=None, level=0) -> str:
        node = node or self._root

        result = ("\t" * level + "`- " + shorten(node) + " ("
            + str(self._depth.get(node, 0)) + ")\n")
        for child in self.children(node):
            result += self.__str__(node=child, level=level + 1)
        return result

    @property
    def root(self) -> Node:
        return self._root

    def depth(self, node: Node) -> int:
        d = self._depth.get(node)
        if d:
            return d
        elif node == self.root:
            return 0
        else:
            raise error.Key("node does not exist")

    def parent(self, node: Node) -> Node | None:
        return self._parents.get(node)

    def children(self, node: Node) -> list[Node]:
        # Not the most efficient, but fine for our purposes since trees will be
        # small and we hardly ever need to query for children
        return [k for k, v in self._parents.items() if v == node]

    def contains(self, node: Node):
        return node == self.root or node in self._parents

    def subsumes(self, superconcept: Node, concept: Node) -> bool:
        parent = self.parent(concept)
        return concept == superconcept or \
            bool(parent and self.subsumes(superconcept, parent))

    def add(self, parent: Node, child: Node):
        if child == self.root:
            raise error.Cycle()

        parent_depth = self._depth.get(parent, 0)
        if parent_depth == 0 and parent != self.root:
            raise error.DisconnectedTree()

        if not self.contains(child):
            self._parents[child] = parent
            self._depth[child] = parent_depth + 1
        elif parent != child:
            # If the child already exists, things get hairy. We can overwrite
            # the current parent relation, but ONLY if the new depth is deeper
            # AND the new parent is subsumed by the old parent anyway AND we
            # don't introduce cycles

            old_depth = self._depth[child]
            old_parent = self._parents[child]
            new_parent = parent
            new_depth = parent_depth + 1

            if new_depth >= old_depth:

                if not self.subsumes(old_parent, new_parent):
                    raise error.NonUniqueParents(child, new_parent, old_parent)

                if self.subsumes(child, new_parent):
                    raise error.Cycle()

                self._parents[child] = new_parent
                self._depth[child] = new_depth

    @staticmethod
    def from_graph(ontology: Graph, root: Node,
            predicate: Node = RDFS.subClassOf) -> Dimension:

        result = Dimension(root)

        def f(node):
            for child in ontology.subjects(predicate, node):
                try:
                    result.add(node, child)
                    f(child)
                except error.NonUniqueParents as e:
                    logging.warning(
                        "{new} will not be a superclass of {child} in the "
                        "taxonomy tree of {dim}; no subsumption with the "
                        "existing superclass {old}".format(
                            new=shorten(e.new),
                            old=shorten(e.old),
                            child=shorten(e.child),
                            dim=shorten(root)
                        )
                    )

        f(root)
        return result
