#!/usr/bin/env python3
"""
Translate output of the natural language parser to a query.
"""

import sys
import json
from rdflib import BNode, RDF
from transformation_algebra import TA
from transformation_algebra.type import Top
from transformation_algebra.graph import TransformationGraph
from transformation_algebra.query import TransformationQuery
from cct import cct


def process(question: dict):
    base = question['cctrans']

    g = TransformationGraph(cct, with_noncanonical_types=False)
    task = BNode()
    types = {}
    for x in base['types']:
        types[x['id']] = x
        x['node'] = node = BNode()
        t = g.add_type(cct.parse_type(x['cct']).concretize(Top))
        g.add((node, TA.type, t))

    for edge in base['transformations']:
        for before in edge['before']:
            for after in edge['after']:
                b = types[before]['node']
                a = types[after]['node']
                g.add((b, TA["from"], a))

    g.add((task, RDF.type, TA.Task))
    g.add((task, TA.output, types['0']['node']))
    q = TransformationQuery(cct, g)
    print(q.sparql(), '\n')


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        for question in json.load(f):
            process(question)
