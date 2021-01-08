# -*- coding: utf-8 -*-
"""
Takes an OWL 2 ontology and adds subClassOf triples by materializing OWL 2 RL
inferences. Removes other triples. Used as input for workflow reasoning.

@author: Schei008
@date: 2019-03-22
@copyright: (c) Schei008 2019
@license: MIT
"""

from __future__ import annotations

from rdf_namespaces import TOOLS, ADA, CCD

import rdflib
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import Graph, URIRef, BNode
from rdflib.term import Node
import logging

import owlrl

from typing import Iterable, List


class Ontology(Graph):
    """
    An ontology is simply an RDF graph.
    """

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)


class Taxonomy(Ontology):
    """
    A taxonomy is an RDF graph consisting of rdfs:subClassOf statements.
    """

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)

    def dimensionality(self, concept: URIRef,
                       dimensions: Iterable[URIRef]) -> int:
        """
        How many dimensions is the given concept subsumed by?
        """
        return sum(1 for d in dimensions if self.subsumed_by(concept, d))

    def expand(self) -> None:
        """
        Expand deductive closure under RDFS semantics.
        """
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self)

    def subsumed_by(self, concept: URIRef, superconcept: URIRef) -> bool:
        """
        Is a concept subsumed by a superconcept in this taxonomy?
        """
        return any(
            s == superconcept or self.subsumed_by(s, superconcept)
            for s in self.objects(subject=concept, predicate=RDFS.subClassOf))

    def core(self, dimensions: List[URIRef]) -> Taxonomy:
        """
        This method generates a taxonomy where nodes intersecting with more
        than one dimension (= not core) are removed. This is needed because APE
        should reason only within any of the dimensions.
        """

        result = Taxonomy()
        for (s, p, o) in self.triples((None, RDFS.subClassOf, None)):
            if self.dimensionality(s, dimensions) == 1:
                result.add((s, p, o))
        return result

    def leaves(self) -> List[Node]:
        """
        Determine the exterior nodes of a taxonomy.
        """
        return [
            n for n in self.subjects(predicate=RDFS.subClassOf, object=None)
            if not (None, RDFS.subClassOf, n) in self]


def clean_owl_ontology(ontology: Graph, dimensions: Iterable[URIRef]):
    """
    This method takes some ontology and returns a taxonomy (consisting only of
    rdfs:subClassOf statements)
    """

    taxonomy = Taxonomy()

    # Turn ontology into taxonomy by keeping only subclass relations
    relevant = Taxonomy()
    relevant += ontology.triples((None, RDFS.subClassOf, None))
    relevant += ontology.triples((None, RDF.type, OWL.Class))

    # Only keep nodes intersecting with exactly one dimension
    for (s, p, o) in relevant:
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing and \
                taxonomy.dimensionality(s, dimensions) == 1:
            taxonomy.add((s, p, o))

    # Add common upper class for all data types
    taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

    return taxonomy


def extract_tool_ontology(tools: Graph):
    """
    Extracts a taxonomy of toolnames from the tool description.
    """

    taxonomy = Taxonomy()
    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        taxonomy.add((o, RDFS.subClassOf, s))
        taxonomy.add((s, RDF.type, OWL.Class))
        taxonomy.add((o, RDF.type, OWL.Class))
        taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))
    return taxonomy
