"""
A semantic type is 

These methods are used to construct semantic dimensions (subsumption trees) for
a given list of superconcepts that identify these dimensions. It returns a
projection function which projects any subsumed node to all given dimensions.
None is returned if the node cannot be projected to this dimension. The method
is used to clean annotations such that we can represent them as a conjunction
of concepts from different semantic dimensions.
"""

from __future__ import annotations

from rdflib import URIRef
from typing import List, Dict, Optional, Set, Iterable

from quangis.taxonomy import Taxonomy
from quangis.namespace import CCD
from quangis.util import shorten


class SemType:
    """
    Ontological classes of semantic types for input and output data across
    different semantic dimensions.
    """

    def __init__(
            self,
            mapping: Optional[Dict[URIRef, Set[URIRef]]] = None):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """

        if mapping:
            self._mapping = mapping
        else:
            self._mapping = {}

    def __getitem__(self, dimension: URIRef) -> Set[URIRef]:
        if dimension in self._mapping:
            return self._mapping[dimension]
        else:
            x: Set[URIRef] = set()
            self._mapping[dimension] = x
            return x

    def __setitem__(self, dimension: URIRef, value: Set[URIRef]) -> None:
        self._mapping[dimension] = value

    def __str__(self) -> str:
        return "{{{}}}".format(
            "; ".join(
                "{} = {}".format(
                    shorten(dimension),
                    ", ".join(shorten(c) for c in classes)
                )
                for dimension, classes in self._mapping.items()
            )
        )

    def to_dict(self) -> Dict[URIRef, List[URIRef]]:
        return {
            d: list(subclasses)
            for d, subclasses in self._mapping.items()
            if subclasses
        }

    def downcast(self) -> SemType:
        """
        Return a new SemType in which certain nodes are downcast to
        identifiable leaf nodes. APE has a closed world assumption, in that it
        considers the set of leaf nodes it knows about as exhaustive: it will
        never consider branch nodes as valid answers.
        """

        return SemType({
            dimension: set(self._downcast.get(n, n) for n in classes)
            for dimension, classes in self._mapping.items()
        })

    _downcast = {
        CCD.NominalA: CCD.PlainNominalA,
        CCD.OrdinalA: CCD.PlainOrdinalA,
        CCD.IntervalA: CCD.PlainIntervalA,
        CCD.RatioA: CCD.PlainRatioA
    }

    @staticmethod
    def project(
            dimensions: List[Taxonomy],
            types: Iterable[URIRef],
            fallback_to_root: bool = True) -> SemType:
        """
        This method projects given nodes to all dimensions given as a list of
        dimensions. Any node that is subsumed by at least one tree can be
        projected to the closest parent in that tree which belongs to its core.
        If a node cannot be projected to a given dimension, then project maps
        to None. This method takes some (subsumption) taxonomy and a list of
        supertypes for each dimension. It constructs a tree for each dimension
        and returns a projection of all nodes that intersect with one of these
        dimensions into the core of the dimension.
        """

        result = SemType()

        for dimension in dimensions:
            dim = dimension.root
            for node in types:
                # If a node is not core (it is subsumed by other dimensions),
                # then we project to the closest parent that *is* core

                projected_node = node

                while projected_node and \
                        any(other_dimension.contains(projected_node)
                            for other_dimension in dimensions
                            if other_dimension is not dimension):
                    projected_node = dimension.parent(projected_node)
                if projected_node:
                    result[dim].add(projected_node)

            # If there is no suitable node, just project to the root of the
            # dimension
            if fallback_to_root and not result[dim]:
                result[dim] = {dim}
        return result
