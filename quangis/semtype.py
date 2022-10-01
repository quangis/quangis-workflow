"""
A semantic type is a mapping between type dimensions and corresponding types.

These methods are used to construct semantic dimensions (subsumption trees) for
a given list of superconcepts that identify these dimensions. It returns a
projection function which projects any subsumed node to all given dimensions.
None is returned if the node cannot be projected to this dimension. The method
is used to clean annotations such that we can represent them as a conjunction
of concepts from different semantic dimensions.
"""

from __future__ import annotations

from rdflib import Graph
from rdflib.term import Node
from typing import Iterable, MutableMapping, Iterator

from quangis.namespace import CCD, RDFS
from quangis.util import shorten


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

    def contains(self, node: Node) -> bool:
        return (node, None, None) in self or (None, None, node) in self

    def parents(self, node: Node) -> Iterable[Node]:
        return self.objects(node, RDFS.subClassOf)

    def subsume(self, subclass: Node, superclass: Node) -> bool:
        return (subclass, RDFS.subClassOf, superclass) in self \
            or any(self.subsume(parent, superclass)
                for parent in self.parents(subclass))


# TODO there can be multiple things in a single dimension?
class SemType(MutableMapping[Dimension, set[Node]]):
    """
    Ontological classes of semantic types for input and output data across
    different semantic dimensions.
    """

    def __init__(self, *dimensions: Dimension):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """
        super().__init__()
        self.data: dict[Dimension, set[Node]] = {d: set() for d in dimensions}

    def __len__(self) -> int:
        return len(self.data)

    def __delitem__(self, k: Dimension) -> None:
        del self.data[k]

    def __iter__(self) -> Iterator[Dimension]:
        return iter(self.data)

    def __getitem__(self, k: Dimension | Node) -> set[Node]:
        return self.data.__getitem__(
            k if isinstance(k, Dimension) else self.dimension(k))

    def __setitem__(self, k: Dimension | Node, v: set[Node]) -> None:
        return self.data.__setitem__(
            k if isinstance(k, Dimension) else self.dimension(k), v)

    def dimension(self, key: Node) -> Dimension:
        """
        Convert the root of a dimension to the corresponding dimension.
        """
        key, = (d for d in self.data.keys() if d.root == key)
        assert isinstance(key, Dimension)
        return key

    def __str__(self) -> str:
        return "{{{}}}".format(
            "; ".join(
                "{} = {}".format(
                    shorten(dimension.root),
                    ", ".join(shorten(c) for c in classes)
                )
                for dimension, classes in self.data.items()
            )
        )

    def downcast(self, target={
            CCD.NominalA: CCD.PlainNominalA,
            CCD.OrdinalA: CCD.PlainOrdinalA,
            CCD.IntervalA: CCD.PlainIntervalA,
            CCD.RatioA: CCD.PlainRatioA}) -> SemType:
        """
        APE has a closed world assumption, in that it considers the set of leaf
        nodes it knows about as exhaustive. This method returns a new `SemType`
        in which certain branch nodes are cast to identifiable leaf nodes, so
        that they can be considered as valid answers.
        """
        for dimension, classes in self.items():
            self[dimension] = set(target.get(n, n) for n in classes)
        return self

    @staticmethod
    def project(dimensions: Iterable[Dimension], types: Iterable[Node]) -> SemType:
        """
        Projects type nodes to the given dimensions. Any type that is subsumed
        by at least one dimension can be projected to the closest parent(s) in
        the corresponding taxonomy graph which belongs to the core of that
        dimension (ie a node that belongs to exactly one dimension).
        """

        result = SemType(*dimensions)

        for d in dimensions:
            other_dimensions = list(d2 for d2 in dimensions if d2 is not d)
            for node in types:
                projection: list[Node] = []
                if not d.contains(node):
                    continue

                stack = [node]
                while len(stack) > 0:
                    current = stack.pop()
                    if any(d2.contains(current) for d2 in other_dimensions):
                        stack.extend(d.parents(current))
                    else:
                        if not any(d.subsume(p, current) for p in projection):
                            projection.append(current)

                result[d].update(projection)
        return result
