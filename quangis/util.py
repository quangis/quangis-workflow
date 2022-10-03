"""
Various utility functions.
"""

import os
import sys
import urllib.request
from pathlib import Path
from rdflib import URIRef, BNode, Literal
from rdflib.term import Node
from typing import Iterator

from quangis.dimtypes import Dimension, DimTypes
from quangis.namespace import namespaces

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


def get_data(fn: Path, dimensions: list[Dimension]) -> Iterator[DimTypes]:
    """
    Read a newline-separated file of type nodes represented by comma-separated
    URIs.
    """
    with open(fn, 'r') as f:
        for line in f.readlines():
            types = list(uri(t)
                for x in line.split("#")[0].split(",") if (t := x.strip()))
            dt = DimTypes(*dimensions)
            for t, d in zip(types, dimensions):
                dt[d].add(t)
            yield dt


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
