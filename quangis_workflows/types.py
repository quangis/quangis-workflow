"""
This module defines a multi-dimensional type, which is a mapping between
dimensions of semantic types, and an intersection of types from that dimension.
"""

from __future__ import annotations

from rdflib import Graph
from rdflib.term import Node, URIRef
from rdflib.namespace import Namespace
from typing import Iterable, MutableMapping, Iterator, Mapping

from quangis_workflows.namespace import RDFS, namespace_manager

nm = namespace_manager()


class Dimension(Graph):
    """
    A semantic dimension is a directed acyclic graph of classes belonging to 
    that dimension. The graph represents the subclass structure.
    """

    def __init__(self, root: Node, source: Graph,
            namespace: Namespace | None = None):
        super().__init__()
        assert isinstance(root, URIRef)
        self.root: URIRef = root
        if namespace:
            self.bind("", namespace)

        def f(node):
            for child in source.subjects(RDFS.subClassOf, node):
                # TODO catch cycles
                self.add((child, RDFS.subClassOf, node))
                f(child)

        f(root)

    def contains(self, node: Node) -> bool:
        return (node, None, None) in self or (None, None, node) in self

    def parents(self, node: Node) -> Iterable[URIRef]:
        return self.objects(node, RDFS.subClassOf)  # type: ignore

    def subsume(self, subclass: Node, superclass: Node) -> bool:
        return (subclass, RDFS.subClassOf, superclass) in self \
            or any(self.subsume(parent, superclass)
                for parent in self.parents(subclass))


class Polytype(MutableMapping[Dimension, set[URIRef]]):
    """
    A single type representing types across multiple semantic dimensions.
    """

    def __init__(self,
            dimensions: Iterable[Dimension]
                | Mapping[Dimension, Iterable[URIRef]],
            types: Iterable[URIRef] | None = None):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """
        super().__init__()
        self.data: dict[Dimension, set[URIRef]]

        if types is not None:
            self.data = {k: {t} for k, t in zip(dimensions, types)}
        elif isinstance(dimensions, Mapping):
            self.data = {k: set(v) for k, v in dimensions.items()}
        else:
            self.data = {k: set() for k in dimensions}

    def __str__(self) -> str:
        return str({str(k.root): list(v) for k, v in self.items()})

    def __repr__(self) -> str:
        return str(self)

    def short(self, separator: str = "&") -> str:
        types = set(x for xs in self.data.values() for x in xs)
        return separator.join(sorted(t.n3(nm) for t in types))

    def __len__(self) -> int:
        return len(self.data)

    def __delitem__(self, k: Dimension) -> None:
        del self.data[k]

    def __iter__(self) -> Iterator[Dimension]:
        return iter(self.data)

    def __getitem__(self, k: Dimension | Node) -> set[URIRef]:
        d = k if isinstance(k, Dimension) else self.dimension(k)
        return self.data.__getitem__(d)  # or {d.root} to fall back to root

    def __setitem__(self, k: Dimension | Node, v: set[URIRef]) -> None:
        return self.data.__setitem__(
            k if isinstance(k, Dimension) else self.dimension(k), v)

    def dimension(self, key: Node) -> Dimension:
        """
        Convert the root of a dimension to the corresponding dimension.
        """
        key, = (d for d in self.data.keys() if d.root == key)
        assert isinstance(key, Dimension)
        return key

    def downcast(self, mapping: Mapping[URIRef, URIRef]) -> Polytype:
        """
        APE has a closed world assumption, in that it considers the set of leaf
        nodes it knows about as exhaustive. This method can be used to cast
        certain branch nodes to identifiable leaf nodes, so that they can be
        considered as valid answers.
        """
        for dimension, classes in self.items():
            self[dimension] = set(mapping.get(n, n) for n in classes)
        return self

    @staticmethod
    def project(dimensions: Iterable[Dimension],
            types: Iterable[Node]) -> Polytype:
        """
        Projects type nodes to the given dimensions. Any type that is subsumed
        by at least one dimension can be projected to the closest parent(s) in
        the corresponding taxonomy graph which belongs to the core of that
        dimension (ie a node that belongs to exactly one dimension).
        """

        dimensions, types = list(dimensions), list(types)
        result = Polytype(dimensions)

        for d in dimensions:
            other_dimensions = list(d2 for d2 in dimensions if d2 is not d)
            for node in types:
                assert isinstance(node, URIRef)
                projection: list[URIRef] = []
                if not d.contains(node):
                    continue

                stack: list[URIRef] = [node]
                while len(stack) > 0:
                    current = stack.pop()
                    if any(d2.contains(current) for d2 in other_dimensions):
                        stack.extend(d.parents(current))
                    else:
                        if not any(d.subsume(p, current) for p in projection):
                            projection.append(current)

                result[d].update(projection)
            if not result[d]:
                result[d] = {d.root}
        return result

    @staticmethod
    def assign(dimensions: Iterable[Dimension],
            types: Iterable[Node]) -> Polytype:
        """
        An alternative constructor, like `project`, but without the magic.
        """
        dimensions, types = list(dimensions), list(types)
        result = Polytype(dimensions)
        for d in dimensions:
            for t in types:
                if d.contains(t):
                    result[d].add(t)
        return result
