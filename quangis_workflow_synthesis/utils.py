"""
Various utility functions.
"""

import os.path
import rdflib
import urllib.request
import logging


def load_rdf(path, format=None):
    """
    Load an RDF graph from a file.
    """

    g = rdflib.Graph()
    g.parse(path, format=format or rdflib.util.guess_format(path))
    return g


def download_if_missing(path, url):
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    if not os.path.isfile(path):
        logging.warning(
            "{} not found; now downloading from {}".format(path, url))
        urllib.request.urlretrieve(url, filename=path)

    return path
