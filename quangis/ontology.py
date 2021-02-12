"""
Methods and datatypes to manipulate ontologies.
"""

from __future__ import annotations

import rdflib
import owlrl
from rdflib import Graph, URIRef
from rdflib.term import Node
from typing import Iterable, List

from quangis.namespace import RDFS, namespaces


class Ontology(Graph):
    """
    An ontology is simply an RDF graph.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for prefix, ns in namespaces.items():
            self.bind(prefix, str(ns))

    def dimensionality(self, concept: URIRef,
                       dimensions: Iterable[URIRef]) -> int:
        """
        By how many dimensions is the given concept subsumed?
        """
        return sum(1 for d in dimensions if self.subsumed_by(concept, d))

    def expand(self) -> None:
        """
        Expand deductive closure under RDFS semantics.
        """
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self)

    def subsumed_by(self, concept: URIRef, superconcept: URIRef) -> bool:
        """
        Is a concept subsumed by a superconcept in this ontology?
        """
        # TODO assumes that RDFS.subClassOf graph is not cyclical
        return concept == superconcept or any(
            s == superconcept or self.subsumed_by(s, superconcept)
            for s in self.objects(subject=concept, predicate=RDFS.subClassOf))

    def leaves(self) -> List[Node]:
        """
        Determine the exterior nodes of a taxonomy.
        """
        return [
            n for n in self.subjects(predicate=RDFS.subClassOf, object=None)
            if not (None, RDFS.subClassOf, n) in self]

    @staticmethod
    def from_rdf(path: str, format: str = None) -> Ontology:
        g = Ontology()
        g.parse(path, format=format or rdflib.util.guess_format(path))
        return g
