"""
Various utility functions.
"""

from rdflib import URIRef, BNode, Literal
from rdflib.term import Identifier

from quangis import namespace


def shorten(node: Identifier) -> str:
    """
    Return RDF node as string, possibly shortened.
    """

    if type(node) == URIRef:
        uri = str(node)
        for short, full in namespace.mapping.items():
            full = str(full)
            if uri.startswith(full):
                return "{}:{}".format(short, uri[len(full):])
        return uri
    elif type(node) == BNode:
        return "(blank)"
    elif type(node) == Literal:
        return "\"{}\"".format(node)
    return str(node)


def uri(string: str) -> URIRef:
    """
    Convert a possibly shortened string to a URIRef.
    """
    for prefix, ns in namespace.mapping.items():
        if string.startswith(prefix + ":"):
            return getattr(ns, string[len(prefix)+1:])
    return URIRef(string)

