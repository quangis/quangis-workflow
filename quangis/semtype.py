"""
These methods are used to construct semantic dimensions (subsumption trees) for
a given list of superconcepts that identify these dimensions. It returns a
projection function which projects any subsumed node to all given dimensions.
None is returned if the node cannot be projected to this dimension. The method
is used to clean annotations such that we can represent them as a conjunction
of concepts from different semantic dimensions.

Note: Internally, the method turns a subsumption DAG into a tree. Since this is
in general non-unique (see Topological ordering of a DAG), the method is
deterministic only when the subsumption graph is in its raw form (similar to a
tree). It should not be used on subsumption graphs that were closed with
reasoning. The graph needs to contain a minimal set of subsumption relations.
"""

from ontology import Taxonomy
from namespace import CCD, EXM, shorten

import rdflib
from rdflib.namespace import RDFS
from rdflib import Graph, URIRef
from rdflib.term import Node
from collections import defaultdict
from typing import Iterable, List, Mapping, Dict, Optional
import logging


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
                for dimension, classes in self.mapping.items()
            )
        )

    @property
    def mapping(self) -> Dict[URIRef, List[URIRef]]:
        return {
            d: subclasses
            for d, subclasses in self._mapping.items() if subclasses
        }


def project(
        taxonomy: Taxonomy,
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
    subsumptions = {d: taxonomy.subsumptions(d) for d in dimensions}

    for node in taxonomy.objects():
        semtype = SemType()
        for d, s in subsumptions.items():
            # If a node is not core (it is also subsumed by other trees), then
            # we project to the closest parent that *is* core
            n = node
            while n is not None \
                    and any(t.contains(n) for t in subsumptions.values() if t is not s):
                n = s.value(object=n, predicate=RDFS.subClassOf)
                # TODO cyclical subClassOf relations aren't very sensical, but
                # will probably crash this
            if n:
                semtype[d].append(n)
        projection[node] = semtype

    return projection

