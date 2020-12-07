# -*- coding: utf-8 -*-
"""
Takes an OWL 2 ontology and adds subClassOf triples by materializing OWL 2 RL
inferences. Removes other triples. Used as input for workflow reasoning.

@author: Schei008
@date: 2019-03-22
@copyright: (c) Schei008 2019
@licence: MIT
"""

import rdflib
from rdflib.namespace import RDFS, RDF, OWL
from rdflib import BNode

TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
ADA = rdflib.Namespace("http://geographicknowledge.de/vocab/AnalysisData.rdf#")
CCD = rdflib.Namespace(
    "http://geographicknowledge.de/vocab/CoreConceptData.rdf#")
EXT = rdflib.Namespace(
    "http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#")
"""Helper stuff"""


def load_rdf(g, rdffile, format='turtle'):
    #print("load_ontologies")
    #print("  Load RDF file: "+fn)
    g.parse(rdffile, format=format)
    n_triples(g)
    return g


"""Reasoning stuff"""


def run_inferences(g):
    #print('run_inferences')
    # expand deductive closure
    #owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    #owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
    n_triples(g)
    return g


def n_triples(g, n=None):
    """ Prints the number of triples in graph g """
    if n is None:
        print(('  Triples: ' + str(len(g))))
    else:
        print(('  Triples: +' + str(len(g) - n)))
    return len(g)


#Checks if concept is subsumed by concept in graph
#def subsumedby(concept, superconcept, graph):
#    out = False
#    for s in graph.objects(subject=concept, predicate=RDFS.subClassOf):
#        if s == superconcept:
#            out= True
#        else:
#            out = subsumedby(s,superconcept,graph)
#        if out:
#            break
#    return out
#
#def testDimensionality(concept,dimnodes,graph):
#    nodim = 0
#    for dim in dimnodes:
#        if subsumedby(concept, dim, graph):
#            nodim+=1
#    return nodim
"""This method takes some ontology in Turtle and returns a taxonomy (consisting only of rdfs:subClassOf statements)"""


def cleanOWLOntology(ontologyfile='CoreConceptData_ct.ttl'
                     ):  #This takes the combined types version as input
    print('Clean OWL ontology!')
    ccdontology = load_rdf(rdflib.Graph(), ontologyfile)
    print('Running inferences:')
    ccdontology = run_inferences(ccdontology)
    taxonomy = rdflib.Graph()
    print('Extracting subClassOf triples:')
    taxonomy += ccdontology.triples(
        (None, RDFS.subClassOf,
         None))  #Keeping only subClassOf statements and classes
    taxonomy += ccdontology.triples((None, RDF.type, OWL.Class))
    n_triples(taxonomy)
    print(
        'Cleaning blank node triples and loops, as well as nodes intersecting more than 1 dimenion'
    )
    taxonomyclean = rdflib.Graph()
    for (
            s, p, o
    ) in taxonomy:  #Removing triples that stem from blanknodes as well as loops
        if type(s) != BNode and type(o) != BNode:
            if s != o and s != OWL.Nothing:
                #if p==RDFS.subClassOf: #Removing nodes intersecting with more or less than one of the given dimensions
                #   if testDimensionality(s,dimnodes,taxonomy)==1:
                taxonomyclean.add((s, p, o))

    n_triples(taxonomyclean)
    #add common upper class for all data types, including spatial attributes and spatial data sets. They are not needed otherwise
    taxonomyclean.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomyclean.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomyclean.add((ADA.Quality, RDFS.subClassOf, CCD.DType))
    return taxonomyclean


"""Extracts a taxonomy of toolnames from the tool description."""


def extractToolOntology(tooldesc='ToolDescription_ct.ttl'):
    print('Extract Tool ontology!')
    output = rdflib.Graph()
    tools = load_rdf(rdflib.Graph(), tooldesc)
    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        output.add((o, RDFS.subClassOf, s))
        output.add((s, RDF.type, OWL.Class))
        output.add((o, RDF.type, OWL.Class))
        #add common upper class for all tool types
        output.add((s, RDFS.subClassOf, TOOLS.Tool))
    n_triples(output)
    return output


def main(ontologyfile='CoreConceptData.ttl',
         tooldesc='ToolDescription.ttl',
         to='ToolDescription_tax.ttl',
         dto='CoreConceptData_tax.ttl'):
    tax = cleanOWLOntology(ontologyfile)
    tooltax = extractToolOntology(tooldesc=tooldesc)
    tax.serialize(destination=dto, format="turtle")
    tooltax.serialize(destination=to, format="turtle")


if __name__ == '__main__':
    main()
