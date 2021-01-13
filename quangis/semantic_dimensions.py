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
from typing import Iterable, List, Mapping, Dict
import logging


SemTypeDict = Dict[URIRef, List[URIRef]]


class SemType:
    """
    Ontological classes of input or output datatypes across different semantic
    dimensions.
    """

    def __init__(self, mapping: SemTypeDict):
        """
        We represent a datatype as a mapping from RDF dimension nodes to one or
        more of its subclasses.
        """
        self._mapping = mapping

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


def project(
        taxonomy: Taxonomy,
        dimensions: List[URIRef]) -> Dict[URIRef, Dict[URIRef, URIRef]]:
    """
    This method projects given nodes to all dimensions given as a list of
    dimensions (as subsumption trees). Any node that is subsumed by at least
    one tree can be projected to the closest parent in that tree which belongs
    to its core. If a node cannot be projected to a given dimension, then
    project maps to None.
    This method takes some (subsumption) taxonomy and a list of supertypes for
    each dimension. It constructs a tree for each dimension and returns a
    projection of all nodes that intersect with one of these dimensions into
    the core of the dimension. It also generates a corresponding core taxonomy
    (containing only core classes for each dimension).
    """

    projection: Dict[URIRef, Dict[URIRef, URIRef]] = {}
    subsumptions = {d: taxonomy.subsumptions(d) for d in dimensions}

    for node in taxonomy.objects():
        n = {d: None for d in dimensions}
        for d, s in subsumptions.items():
            # If a node is not core (it is also subsumed by other trees), then
            # we project to the closest parent that *is* core
            p = node
            while p is not None \
                    and any(s.contains(p) for t in subsumptions if t is not s):
                parent = s.value(object=p, predicate=RDFS.subClassOf)
                p = parent
            n[d] = p

        projection[node] = n

    return projection

