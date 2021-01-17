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
from typing import List, Dict, Optional

from quangis.ontology import Ontology, Taxonomy
from quangis.namespace import CCD
from quangis.util import shorten


class SemType:
    """
    Ontological classes of semantic types for input and output data across
    different semantic dimensions.
    """

    def __init__(self, mapping: Optional[Dict[URIRef, List[URIRef]]] = None):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """
        if mapping:
            self._mapping = mapping
        else:
            self._mapping = {}

    def __getitem__(self, dimension: URIRef) -> List[URIRef]:
        if dimension in self._mapping:
            return self._mapping[dimension]
        else:
            x: List[URIRef] = []
            self._mapping[dimension] = x
            return x

    def __setitem__(self, dimension: URIRef, value: List[URIRef]) -> None:
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

    def as_dictionary(self) -> Dict[URIRef, List[URIRef]]:
        return {
            d: subclasses
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
            dimension: [self._downcast.get(n, n) for n in classes]
            for dimension, classes in self._mapping.items()
        })

    _downcast = {
        CCD.NominalA: CCD.PlainNominalA,
        CCD.OrdinalA: CCD.PlainOrdinalA,
        CCD.IntervalA: CCD.PlainIntervalA,
        CCD.RatioA: CCD.PlainRatioA
    }


def project(
        ontology: Ontology,
        dimensions: List[URIRef]) -> Dict[URIRef, SemType]:
    """
    This method projects given nodes to all dimensions given as a list of
    dimensions. Any node that is subsumed by at least one tree can be projected
    to the closest parent in that tree which belongs to its core. If a node
    cannot be projected to a given dimension, then project maps to None.
    This method takes some (subsumption) taxonomy and a list of supertypes for
    each dimension. It constructs a tree for each dimension and returns a
    projection of all nodes that intersect with one of these dimensions into
    the core of the dimension. It also generates a corresponding core taxonomy
    (containing only core classes for each dimension).
    """

    projection: Dict[URIRef, SemType] = {}

    subsumptions = [Taxonomy.from_ontology(ontology, d) for d in dimensions]

    for node in ontology.subjects():
        result = SemType()
        for tree in subsumptions:
            # If a node is not core (it is also subsumed by other trees), then
            # we project to the closest parent that *is* core

            projected_node = node
            while projected_node and \
                    any(other_tree.contains(projected_node) for other_tree in
                        subsumptions if other_tree is not tree):
                projected_node = tree.parent(projected_node)

            if projected_node:
                dimension = tree.root
                result[dimension].append(projected_node)

        projection[node] = result

    return projection

