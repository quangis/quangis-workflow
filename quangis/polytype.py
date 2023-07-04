"""
This module defines a multi-dimensional type, which is a mapping between
dimensions of semantic types, and an intersection of types from that dimension.
"""

from __future__ import annotations

from rdflib import Graph
from rdflib.term import Node, URIRef
from rdflib.namespace import Namespace
from typing import Iterable, MutableMapping, Iterator, Mapping
from itertools import product

from quangis.namespace import RDFS, n3
from transforge.namespace import shorten


class Dimension(object):
    """A semantic dimension is a directed acyclic graph of classes belonging to 
    that dimension. The graph represents the subclass structure."""

    def __init__(self, root: Node,
            source: Graph | Mapping[URIRef, Iterable[URIRef]],
            namespace: Namespace | None = None):
        super().__init__()

        assert isinstance(root, URIRef)
        self.root: URIRef = root
        self.graph: Graph = Graph()

        if namespace:
            self.graph.bind("", namespace)

        def f(node):
            if isinstance(source, Graph):
                children = source.subjects(RDFS.subClassOf, node)
            else:
                try:
                    children = source[node]
                except KeyError:
                    children = ()

            for child in children:
                self.graph.add((child, RDFS.subClassOf, node))
                if (None, None, child) not in self.graph:
                    f(child)
        f(root)

    def __contains__(self, node: Node) -> bool:
        return (node == self.root
            or ((node, RDFS.subClassOf, None)) in self.graph)

    def parents(self, node: Node) -> Iterable[URIRef]:
        return self.graph.objects(node, RDFS.subClassOf)  # type: ignore

    def subsume(self, subclass: Node, superclass: Node,
            strict: bool = False) -> bool:
        return (
            (not strict and subclass == superclass)
            or (subclass, RDFS.subClassOf, superclass) in self.graph
            or any(self.subsume(parent, superclass)
                for parent in self.parents(subclass)))


class Polytype(MutableMapping[URIRef, set[URIRef]]):
    """
    A type representing an intersection of types (represented by RDF nodes) 
    across multiple semantic dimensions.
    """

    def __init__(self,
            dimensions: Iterable[Dimension]
                | Mapping[Dimension, Iterable[URIRef]],
            types: Iterable[Node] = (),
            ignore_extradimensional_types: bool = False):
        """A polytype associates each given dimension with a conjunction of 
        classes in that dimension. This corresponds to the subtaxonomies and 
        classes in the domain ontology of APE; see also:
        <https://ape-framework.readthedocs.io/en/latest/docs/specifications/setup.html#referencing-the-domain-model>

        If `types` is given, each of the given types are simply added to all 
        dimension(s) it's part of."""
        super().__init__()

        # self.dimensions: list[Dimension] = list(dimensions)
        self.dimensions: dict[URIRef, Dimension] = {d.root: d
            for d in dimensions}

        self.data: dict[URIRef, set[URIRef]]

        if isinstance(dimensions, Mapping):
            self.data = {k.root: set(v) for k, v in dimensions.items()}
            if not all(all(v in self.dimensions[k] for v in vs)
                    for k, vs in self.data.items()):
                raise RuntimeError(
                    "Not all given classes are part of their dimension")
        else:
            self.data = {k: set() for k in self.dimensions}

        for t in types:
            in_any_dimension = False
            for d in dimensions:
                if t in d:
                    assert isinstance(t, URIRef)
                    self.data[d.root].add(t)
                    in_any_dimension = True
            if not in_any_dimension and not ignore_extradimensional_types:
                raise RuntimeError(
                    f"Type {t} is not part of any of the given dimensions.")

    def __str__(self) -> str:
        return "; ".join(
            f"{', '.join(n3(v) for v in vs)} (in {n3(k)})"
            for k, vs in self.items()
        )

    def __len__(self) -> int:
        return len(self.data)

    def __delitem__(self, k: Dimension | URIRef) -> None:
        del self.data[k if isinstance(k, URIRef) else k.root]

    def __iter__(self) -> Iterator[URIRef]:
        return iter(self.data)

    def __getitem__(self, k: Dimension | URIRef) -> set[URIRef]:
        dimension = k if isinstance(k, Dimension) else self.dimensions[k]
        return self.data.__getitem__(dimension.root)

    def __setitem__(self, k: Dimension | URIRef, v: Iterable[URIRef]) -> None:
        dimension = k if isinstance(k, Dimension) else self.dimensions[k]
        types = set()
        for t in v:
            if t not in dimension:
                raise RuntimeError
            else:
                types.add(t)
        return self.data.__setitem__(dimension.root, types)

    def empty(self) -> bool:
        """Return True if the type is empty, that is, if every dimension is 
        empty or at the root node."""
        assert self.data.keys()
        return all(not ts or all(t == dim for t in ts)
            for dim, ts in self.data.items())

    def uris(self) -> set[URIRef]:
        return set(x for xs in self.data.values() for x in xs)

    def short(self, separator: str = ", ") -> str:
        return separator.join(sorted(n3(t) for t in self.uris()))

    def downcast(self, mapping: Mapping[URIRef, URIRef]) -> Polytype:
        """This method can be used to cast certain branch nodes to identifiable 
        leaf nodes, so that they can be considered as valid answers. This is 
        useful because APE has a closed world assumption, in that it considers 
        the set of leaf nodes it knows about as exhaustive."""
        for dimension, classes in self.items():
            self[dimension] = set(mapping.get(n, n) for n in classes)
        return self

    def subtype(self, other: Polytype, strict: bool = False) -> bool:
        if self.dimensions != other.dimensions:
            return False

        for k, d in self.dimensions.items():
            if not all(d.subsume(a, b, strict=strict)
                    for a, b in product(self[d], other[d])):
                return False
        return True

    def normalize(self) -> Polytype:
        """A polytype is an intersection of types. The normalization of a 
        polytype simply removes extraneous activations: if β is a subtype of α, 
        then clearly activating β means that the activation of α is implicit 
        and so α can be left out."""
        return Polytype({
            dim: set(
                x for x in self[d]
                if not any(dim.subsume(y, x, strict=True) for y in self[d])
            ) for d, dim in self.dimensions.items()
        })

    def lexical(self) -> tuple[tuple[URIRef, ...], ...]:
        """Obtain a tuple with which to order polytypes."""
        t = self.normalize()
        result: tuple[tuple[URIRef, ...], ...] = ()
        for d in sorted(t.dimensions):
            result += (tuple(sorted(t[d])),)
        return result

    def canonical_name(self) -> str:
        """A polytype can be referred to by a canonical name. Assuming 
        alphanumeric class names, the name should use only characters that are 
        valid in URIs (<https://www.rfc-editor.org/rfc/rfc3986#section-2.3>). A 
        canonical name only makes sense in the context of a given set of 
        dimensions."""
        return ".".join(
            "_".join(shorten(t) for t in ts)
            for ts in self.lexical()
        )

    def projection(self) -> Polytype:
        return Polytype.project(self.dimensions.values(), self.uris())

    @staticmethod
    def project(dimensions: Iterable[Dimension],
            types: Iterable[Node]) -> Polytype:
        """An alternative constructor for a `Polytype` that projects type nodes 
        to the given dimensions. Any type that is subsumed by at least one 
        dimension can be projected to the closest parent(s) in the 
        corresponding taxonomy graph which belongs to the core of that 
        dimension (ie a node that belongs to exactly one dimension)."""

        dimensions, types = set(dimensions), list(types)
        result = Polytype(dimensions)

        for d in dimensions:
            other_dimensions = list(d2 for d2 in dimensions if d2 is not d)
            for node in types:
                assert isinstance(node, URIRef)
                projection: list[URIRef] = []
                if node not in d:
                    continue

                stack: list[URIRef] = [node]
                while len(stack) > 0:
                    current = stack.pop()
                    if any(current in d2 for d2 in other_dimensions):
                        stack.extend(d.parents(current))
                    else:
                        if not any(d.subsume(p, current) for p in projection):
                            projection.append(current)

                result[d].update(projection)
            if not result[d]:
                result[d] = {d.root}
        return result
