#!/usr/bin/env python3
from __future__ import annotations
from rdflib import Graph  # type: ignore

import config  # type: ignore
from queries import all_queries

wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")

for q in all_queries:
    print(q["name"])
    for variant, query in q["variants"].items():
        if not variant.startswith("eval"):
            continue
        print(variant)
        for i, sparql in enumerate(query.sparql_diagnostics()):
            print(i)
            try:
                results = wfgraph.query(sparql)
            except ValueError:
                print("Not sending query")
            else:
                for r in results:
                    print(r.number_of_results)
