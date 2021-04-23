#!/usr/bin/env python3
"""
Visually inspect parse trees for all tool expressions.
"""
import rdflib  # type: ignore
from cct import cct

TOOLS = rdflib.Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
path = "ToolDescription_TransformationAlgebra.ttl"
g = rdflib.Graph()
g.parse(path, format=rdflib.util.guess_format(path))
for s, o in sorted(g.subject_objects(TOOLS.algebraexpression)):
    e = cct.parse(o)
    assert e
    print(s)
    #if any(e.type.variables()):
    print(e.tree())
    #else:
    #    print(e.type)
    print()
