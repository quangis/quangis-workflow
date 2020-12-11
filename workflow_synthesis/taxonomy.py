# -*- coding: utf-8 -*-
"""
Takes an OWL 2 ontology and adds subClassOf triples by materializing OWL 2 RL
inferences. Removes other triples. Used as input for workflow reasoning.

@author: Schei008
@date: 2019-03-22
@copyright: (c) Schei008 2019
@license: MIT
"""

from rdf_namespaces import TOOLS, ADA, CCD

import rdflib
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import BNode
import logging


def run_inferences(g):
    """Reasoning stuff"""
    # expand deductive closure
    # owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    # owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
    return g


# Checks if concept is subsumed by concept in graph
def subsumedby(concept, superconcept, graph):
    out = False
    for s in graph.objects(subject=concept, predicate=RDFS.subClassOf):
        if s == superconcept:
            out = True
        else:
            out = subsumedby(s, superconcept, graph)
        if out:
            break
    return out


def testDimensionality(concept, dimnodes, graph):
    nodim = 0
    for dim in dimnodes:
        if subsumedby(concept, dim, graph):
            nodim += 1
    return nodim


def cleanOWLOntology(ccdontology, dimnodes):
    """
    This method takes some ontology in Turtle and returns a taxonomy
    (consisting only of rdfs:subClassOf statements)
    """

    logging.info("Cleaning OWL ontology...")

    logging.info("Running inferences...")
    ccdontology = run_inferences(ccdontology)
    logging.debug("Number of triples: {}".format(len(ccdontology)))

    logging.info("Extracting subClassOf triples...")
    taxonomy = rdflib.Graph()
    taxonomy += ccdontology.triples((None, RDFS.subClassOf, None))
    taxonomy += ccdontology.triples((None, RDF.type, OWL.Class))
    logging.debug("Number of triples: {}".format(len(taxonomy)))

    logging.debug("Cleaning blank node triples, loops, and nodes"
                  "intersecting more than one dimension")
    taxonomyclean = rdflib.Graph()
    for (s, p, o) in taxonomy:
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing:
            # Removing nodes intersecting with more or less than one of the
            # given dimensions
            # p == RDFS.subClassOf and
            if testDimensionality(s, dimnodes, taxonomy) == 1:
                taxonomyclean.add((s, p, o))
    logging.debug("Number of triples: {}".format(len(taxonomyclean)))

    # add common upper class for all data types, including spatial attributes
    # and spatial data sets. They are not needed otherwise
    taxonomyclean.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomyclean.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomyclean.add((ADA.Quality, RDFS.subClassOf, CCD.DType))
    return taxonomyclean


def extractToolOntology(tools):
    """
    Extracts a taxonomy of toolnames from the tool description.
    """

    logging.info("Extracting tool ontology...")

    output = rdflib.Graph()
    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        output.add((o, RDFS.subClassOf, s))
        output.add((s, RDF.type, OWL.Class))
        output.add((o, RDF.type, OWL.Class))
        # add common upper class for all tool types
        output.add((s, RDFS.subClassOf, TOOLS.Tool))

    logging.debug("Number of triples: {}".format(len(output)))
    return output

