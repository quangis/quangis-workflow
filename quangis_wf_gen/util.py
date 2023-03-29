"""
Various utility functions.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from rdflib import URIRef, BNode, Literal
from rdflib.term import Node

from quangis_wf_gen.namespace import namespaces

root_dir = Path(__file__).parent.parent

def shorten(node: Node) -> str:
    """
    Return RDF node as string, possibly shortened.
    """

    if type(node) == URIRef:
        uri = str(node)
        for short, full in namespaces.items():
            # full = str(full)
            if uri.startswith(full):
                return "{}:{}".format(short, uri[len(full):])
        return uri
    elif type(node) == BNode:
        return "(blank)"
    elif type(node) == Literal:
        return "\"{}\"".format(node)
    return str(node)


# TODO temporary
def uri(short: str) -> URIRef:
    for pre, ns in namespaces.items():
        if short.startswith(pre.lower()):
            return ns[short[len(pre) + 1:]]
    raise RuntimeError


def download(url: str, dest_dir: Path | None = None,
        name: str | None = None) -> Path:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """
    if not dest_dir:
        dest_dir = root_dir
    if not name:
        name = Path(url).name

    assert isinstance(dest_dir, Path)
    path = dest_dir / name
    dest_dir.mkdir(exist_ok=True)
    if not path.exists():
        print(f"{path} not found; now downloading from {url}")
        urllib.request.urlretrieve(url, filename=path)

    return path
