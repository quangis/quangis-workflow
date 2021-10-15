#!/usr/bin/env python3
"""
Generate an RDF vocabulary for the operations and types of CCT.
"""

from transformation_algebra.rdf import TransformationGraph

from cct import cct, CCT
from util import write_graph

cct_vocab = TransformationGraph.vocabulary(cct, CCT)
cct_vocab.bind("cct", CCT)
write_graph(cct_vocab, "cct_vocab")
