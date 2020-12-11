"""
This module holds the RDF namespaces that we use frequently.
"""

import rdflib

_gk = "http://geographicknowledge.de/vocab/"

TEST = rdflib.Namespace("http://www.semanticweb.org/test#")
CCD = rdflib.Namespace(_gk+"CoreConceptData.rdf#")
TOOLS = rdflib.Namespace(_gk+"GISTools.rdf#")
ADA = rdflib.Namespace(_gk+"AnalysisData.rdf#")
EXT = rdflib.Namespace(_gk+"ExtensiveMeasures.rdf#")
WF = rdflib.Namespace(_gk+"Workflow.rdf#")

