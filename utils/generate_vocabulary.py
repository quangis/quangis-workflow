#!/usr/bin/env python3
"""
Generate an RDF vocabulary for the operations and types of CCT.
"""

from transformation_algebra import TransformationGraph

from config import build_path
from cct import cct

vocab = TransformationGraph(cct)
vocab.add_vocabulary()
vocab.serialize(build_path / 'cct.ttl', format='ttl', encoding='utf-8')
