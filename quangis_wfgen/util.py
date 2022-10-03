"""
Various utility functions.
"""

import os
import sys
import urllib.request
from pathlib import Path
from rdflib import URIRef, BNode, Literal
from rdflib.term import Node

from quangis_wfgen.namespace import namespaces

root_dir = Path(__file__).parent.parent
build_dir = root_dir / "build"

if sys.platform.startswith("win"):
    local_dir = Path(os.getenv("LOCALAPPDATA"))
elif sys.platform.startswith("darwin"):
    local_dir = Path("~/Library/Application Support")
elif sys.platform.startswith("linux"):
    local_dir = Path(os.getenv("XDG_DATA_HOME", "~/.local/share"))
else:
    raise RuntimeError("Unsupported platform")


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


def download_if_missing(path: Path, url: str) -> Path:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    directory = path.parent
    directory.mkdir(exist_ok=True)
    if not path.exists():
        print(f"{path} not found; now downloading from {url}")
        urllib.request.urlretrieve(url, filename=path)

    return path
