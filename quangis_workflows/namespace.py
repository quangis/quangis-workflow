"""
This module holds the RDF namespaces that we use frequently.
"""

import sys
from rdflib import Namespace, Graph
from rdflib.term import Node, URIRef
from rdflib.namespace import NamespaceManager
from typing import Mapping
from cct import cct  # type: ignore

TEST = Namespace("http://www.semanticweb.org/test#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
CCD = Namespace("http://geographicknowledge.de/vocab/CoreConceptData.rdf#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
XML = Namespace("http://www.w3.org/XML/1998/namespace")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
EM = Namespace("http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#")
ADA = Namespace("http://geographicknowledge.de/vocab/AnalysisData.rdf#")
WF = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
GIS = Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
# TOOLS = Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
TOOLS = Namespace("https://github.com/quangis/cct/blob/master/tools/tools.ttl#")
REPO = Namespace("https://github.com/quangis/quangis-workflow-generator#")
EX = Namespace('https://example.com/#')
DATA = Namespace("https://github.com/quangis/cct/blob/master/tools/data.ttl#")
CCT_ = Namespace("https://github.com/quangis/cct#")
CCT = cct.namespace

TOOL = Namespace("https://quangis.github.io/tool/vocab#")
SIG = Namespace("https://quangis.github.io/tool/signature#")
SUPERTOOL = Namespace("https://quangis.github.io/tool/super#")


ARC = Namespace("https://pro.arcgis.com/en/pro-app/latest/tool-reference/")
ARCDM = Namespace(ARC + "/data-management/")
ARC3D = Namespace(ARC + "/3d-analyst/")
ARCAN = Namespace(ARC + "/analysis/")
ARCNA = Namespace(ARC + "/network-analyst/")
ARCSA = Namespace(ARC + "/spatial-analyst/")
ARCCO = Namespace(ARC + "/conversion/")

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
    assert isinstance(node, URIRef)
    return node.n3(nm)

def bind_all(g: Graph, default: Namespace | None = None):
    for prefix, namespace in namespaces.items():
        if namespace != default:
            g.bind(prefix, namespace)
        else:
            g.bind("", namespace)
Graph.bind_all = bind_all