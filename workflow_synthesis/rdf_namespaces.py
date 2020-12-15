"""
This module holds the RDF namespaces that we use frequently.
"""

import rdflib
import sys

NAMESPACES = {
    k: rdflib.Namespace(v) for k, v in {
        "test": "http://www.semanticweb.org/test#",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "ccd": "http://geographicknowledge.de/vocab/CoreConceptData.rdf#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xml": "http://www.w3.org/XML/1998/namespace",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "exm": "http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#",
        "em": "http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#",
        "ada": "http://geographicknowledge.de/vocab/AnalysisData.rdf#",
        "wf": "http://geographicknowledge.de/vocab/Workflow.rdf#",
        "gis": "http://geographicknowledge.de/vocab/GISConcepts.rdf#",
        "tools": "http://geographicknowledge.de/vocab/GISTools.rdf#",
    }.items()
}

# Programmatically set namespaces as constants of this module
for k, v in NAMESPACES.items():
    setattr(sys.modules[__name__], k.upper(), v)


def setprefixes(g):
    for k, v in NAMESPACES.items():
        g.bind(k, str(v))
    return g

