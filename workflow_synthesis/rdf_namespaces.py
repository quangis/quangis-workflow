"""
This module holds the RDF namespaces that we use frequently.
"""

import rdflib

_gk = "http://geographicknowledge.de/vocab/"

TEST = rdflib.Namespace("http://www.semanticweb.org/test#")
CCD = rdflib.Namespace(_gk+"CoreConceptData.rdf#")
TOOLS = rdflib.Namespace(_gk+"GISTools.rdf#")
ADA = rdflib.Namespace(_gk+"AnalysisData.rdf#")
EXM = rdflib.Namespace(_gk+"ExtensiveMeasures.rdf#")
WF = rdflib.Namespace(_gk+"Workflow.rdf#")


def setprefixes(g):
    g.bind('foaf', 'http://xmlns.com/foaf/0.1/')
    g.bind('ccd', 'http://geographicknowledge.de/vocab/CoreConceptData.rdf#')
    g.bind('owl', 'http://www.w3.org/2002/07/owl#')
    g.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    g.bind('xml', 'http://www.w3.org/XML/1998/namespace')
    g.bind('xsd', 'http://www.w3.org/2001/XMLSchema#')
    g.bind('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
    g.bind('exm', 'http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#')
    g.bind('ada', 'http://geographicknowledge.de/vocab/AnalysisData.rdf#')
    g.bind('wf', 'http://geographicknowledge.de/vocab/Workflow.rdf#')
    g.bind('gis', 'http://geographicknowledge.de/vocab/GISConcepts.rdf#')
    g.bind('tools', 'http://geographicknowledge.de/vocab/GISTools.rdf#')
    return g
