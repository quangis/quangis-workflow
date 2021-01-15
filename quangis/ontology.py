"""
Methods and datatypes to manipulate ontologies and taxonomies.
"""

from __future__ import annotations

import rdflib
from rdflib import Graph, URIRef, BNode
from rdflib.term import Node
import itertools
import logging
import owlrl
from typing import Iterable, List, Any, Tuple, Optional

from quangis import namespace
from quangis.namespace import TOOLS, ADA, CCD, RDFS, OWL, RDF
from quangis.utils import shorten


class SubsumptionTree(object):
    """
    A subsumption tree is a taxonomy: subclass relations to a single root.
    """

    def __init__(
            self,
            root: URIRef,
            children: List[Tuple[URIRef, Any]],
            parent: Optional[SubsumptionTree] = None):
        self.parent = parent
        self.node = root
        self.children = [SubsumptionTree(*c, parent=root) for c in children]

    def __str__(self, level=0) -> str:
        ret = "\t"*level + "`- " + shorten(self.node) + "\n"
        for child in self.children:
            ret += child.__str__(level+1)
        return ret

    @property
    def root(self) -> SubsumptionTree:
        root = self
        while root.parent:
            root = root.parent
        return root

    @staticmethod
    def from_ontology(ontology: Ontology, root: URIRef) -> SubsumptionTree:
        return SubsumptionTree(
            *rdflib.util.get_tree(ontology, root, RDFS.subClassOf))

    def to_ontology(self) -> Ontology:
        pass


class Ontology(Graph):
    """
    An ontology is simply an RDF graph.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for prefix, ns in namespace.mapping.items():
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
        Is a concept subsumed by a superconcept in this taxonomy?
        """
        return any(
            s == superconcept or self.subsumed_by(s, superconcept)
            for s in self.objects(subject=concept, predicate=RDFS.subClassOf))

    def contains(self, node: Node) -> bool:
        """
        Does this graph contain some node?
        """
        return (node, None, None) in self or (None, None, node) in self

    def leaves(self) -> List[Node]:
        """
        Determine the exterior nodes of a taxonomy.
        """
        return [
            n for n in self.subjects(predicate=RDFS.subClassOf, object=None)
            if not (None, RDFS.subClassOf, n) in self]

    def debug(self) -> None:
        """
        Log this ontology to the console to debug.
        """
        result = [""] + [
            "    {} {} {}".format(shorten(o), shorten(p), shorten(s))
            for (o, p, s) in self.triples((None, None, None))]
        logging.debug("\n".join(result))

    @staticmethod
    def from_rdf(path: str, format: str = None) -> Ontology:
        g = Ontology()
        g.parse(path, format=format or rdflib.util.guess_format(path))
        return g

    def is_taxonomy(self) -> bool:
        """
        A taxonomy is an RDF graph consisting of raw subsumption relations ---
        rdfs:subClassOf statements.
        """
        return all(p == RDFS.subClassOf for p in self.predicates())
        # TODO also, no loops

    def core(self, dimensions: List[URIRef]) -> Ontology:
        """
        This method generates a taxonomy where nodes intersecting with more
        than one dimension (= not core) are removed. This is needed because APE
        should reason only within any of the dimensions.
        """

        result = Ontology()
        for (s, p, o) in self.triples((None, RDFS.subClassOf, None)):
            if self.dimensionality(s, dimensions) == 1:
                result.add((s, p, o))
        return result

    def subsumptions(self, root: URIRef) -> Ontology:
        """
        Take an arbitrary root and generate a new tree with only parent
        relations toward the root. Note that the relations might not be unique.
        """

        result = Ontology()

        def f(node, children):
            for child, grandchildren in children:
                result.add((child, RDFS.subClassOf, node))
                f(child, grandchildren)

        f(*rdflib.util.get_tree(self, root, RDFS.subClassOf))
        return result


def clean_owl_ontology(ontology: Ontology,
                       dimensions: List[URIRef]) -> Ontology:
    """
    This method takes some ontology and returns an OWL taxonomy. (consisting
    only of rdfs:subClassOf statements)
    """

    taxonomy = Ontology()

    # Only keep subclass nodes intersecting with exactly one dimension
    for (o, p, s) in itertools.chain(
            ontology.triples((None, RDFS.subClassOf, None)),
            ontology.triples((None, RDF.type, OWL.Class))
            ):
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing and \
                ontology.dimensionality(o, dimensions) == 1:
            taxonomy.add((o, p, s))

    # Add common upper class for all data types
    taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

    return taxonomy


def extract_tool_ontology(tools: Ontology) -> Ontology:
    """
    Extracts a taxonomy of toolnames from the tool description.
    """

    taxonomy = Ontology()
    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        taxonomy.add((o, RDFS.subClassOf, s))
        taxonomy.add((s, RDF.type, OWL.Class))
        taxonomy.add((o, RDF.type, OWL.Class))
        taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))
    return taxonomy
