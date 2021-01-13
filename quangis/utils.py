"""
Various utility functions.
"""

import os
import os.path
import urllib.request
import logging
from rdflib import URIRef, BNode, Literal
from rdflib.term import Identifier

import namespace


def download_if_missing(path: str, url: str) -> str:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.mkdir(directory)

    if not os.path.isfile(path):
        logging.warning(
            "{} not found; now downloading from {}".format(path, url))
        urllib.request.urlretrieve(url, filename=path)

    return path


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



