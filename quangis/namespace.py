"""
This module holds the RDF namespaces that we use frequently.
"""

import sys
from rdflib import Namespace, Graph
from rdflib.term import Node, URIRef, BNode
from rdflib.namespace import NamespaceManager, RDFS, RDF, OWL, DC
from quangis.cct import CCT
from typing import Mapping

EX = Namespace('https://example.com/#')
CCD = Namespace("http://geographicknowledge.de/vocab/CoreConceptData.rdf#")
ADA = Namespace("http://geographicknowledge.de/vocab/AnalysisData.rdf#")
WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
GIS = Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
TOOLS = Namespace(
    "https://github.com/quangis/cct/blob/master/tools/tools.ttl#")
CCT_ = Namespace("https://github.com/quangis/cct#")

TOOL = Namespace("https://quangis.github.io/vocab/tool#")
ARCGIS = Namespace("https://quangis.github.io/tool#")
MULTI = Namespace("https://quangis.github.io/tool/multi#")
ABSTR = Namespace("https://quangis.github.io/tool/abstract#")

WFGEN = Namespace("https://quangis.github.io/workflows/generated/")
WFEXPERT = Namespace("https://quangis.github.io/workflows/expert/")

ARC = "https://pro.arcgis.com/en/pro-app/latest/tool-reference"
ARCDM = Namespace(ARC + "/data-management/")
ARC3D = Namespace(ARC + "/3d-analyst/")
ARCAN = Namespace(ARC + "/analysis/")
ARCNA = Namespace(ARC + "/network-analyst/")
ARCSA = Namespace(ARC + "/spatial-analyst/")
ARCCO = Namespace(ARC + "/conversion/")
ARCSS = Namespace(ARC + "/spatial-statistics/")

# Also provide a mapping for easy programmatic access
namespaces = {
    k.lower(): v for k, v in sys.modules[__name__].__dict__.items()
    if isinstance(v, Namespace)
}


def namespace_manager(
        namespaces: Mapping[str, Namespace] = namespaces
) -> NamespaceManager:
    _g = Graph()
    for prefix, namespace in namespaces.items():
        _g.bind(prefix.lower(), namespace)
    return NamespaceManager(_g)


def n3(
        node: Node | list[Node] | set[Node],
        nm: NamespaceManager = namespace_manager()
) -> str:
    if isinstance(node, list):
        return f"[{', '.join(n3(x, nm) for x in node)}]"
    elif isinstance(node, set):
        return f"{{{', '.join(n3(x, nm) for x in node)}}}"
    elif isinstance(node, URIRef):
        return node.n3(nm)
    elif isinstance(node, BNode):
        return "<blank node>"
    else:
        raise RuntimeError(f"Cannot express value of type {type(node)}")

def bind_all(g: Graph, default: Namespace | None = None):
    for prefix, namespace in namespaces.items():
        if namespace != default:
            g.bind(prefix, namespace)
        else:
            g.bind("", namespace)
