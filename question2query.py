#!/usr/bin/env python3
"""
Translate output of the natural language parser to a query.
"""

import sys
import json
from rdflib import BNode, RDF
from transformation_algebra import TA
from transformation_algebra.type import Top, Product
from transformation_algebra.graph import TransformationGraph
from transformation_algebra.query import TransformationQuery
from cct import cct, R3


def process(question: dict):
    base = question['cctrans']

    g = TransformationGraph(cct)
    task = BNode()
    types = {}
    for x in base['types']:
        types[x['id']] = x
        x['node'] = node = BNode()
        t = cct.parse_type(x['cct']).concretize(Top)
        if t.params[0].operator == Product:
            t = R3(t.params[0].params[0], t.params[1], t.params[0].params[1])
        try:
            g.add((node, TA.type, cct.uri(t)))
        except ValueError as e:
            print(f"\033[31;1;4mWarning: {e}\033[0m")

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
