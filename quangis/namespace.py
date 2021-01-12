"""
This module holds the RDF namespaces that we use frequently.
"""

import sys
from rdflib import Namespace, URIRef, BNode, Literal
from rdflib.term import Identifier


NAMESPACES = {
    k: Namespace(v) for k, v in {
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


def setprefixes(g):
    """
    Set all known prefixes for an RDF graph.
    """
    for k, v in NAMESPACES.items():
        g.bind(k, str(v))
    return g


def shorten(node: Identifier) -> str:
    """
    Return RDF node as string, possibly shortened.
    """

    if type(node) == URIRef:
        uri = str(node)
        for short, full in NAMESPACES.items():
            full = str(full)
            if uri.startswith(full):
                return "{}:{}".format(short, uri[len(full):])
        return uri
    elif type(node) == BNode:
        return "(blank)"
    elif type(node) == Literal:
        return "\"{}\"".format(node)
    return str(node)


# Programmatically set namespaces as uppercased constants of this module
for k, v in NAMESPACES.items():
    setattr(sys.modules[__name__], k.upper(), v)
