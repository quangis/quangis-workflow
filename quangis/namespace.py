"""
This module holds the RDF namespaces that we use frequently.
"""

import sys
from rdflib import Namespace

TEST = Namespace("http://www.semanticweb.org/test#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
CCD = Namespace("http://geographicknowledge.de/vocab/CoreConceptData.rdf#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
XML = Namespace("http://www.w3.org/XML/1998/namespace")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
EM = Namespace("http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#")
ADA = Namespace("http://geographicknowledge.de/vocab/AnalysisData.rdf#")
WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
GIS = Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
TOOLS = Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
EX = Namespace('https://example.com/#')

# Also provide a mapping for easy programmatic access
namespaces = {
    k.lower(): v for k, v in sys.modules[__name__].__dict__.items()
    if isinstance(v, Namespace)
}
