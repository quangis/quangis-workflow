#!/usr/bin/env python3
"""
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
from rdflib import Graph  # type: ignore
from transformation_algebra.query import Query

from config import query_paths, build_path  # type: ignore


def extract_queries() -> dict[tuple[str, str], Query]:
    """
    Extract queries defined in modules.
    """
    # Perhaps overengineered but makes it simple to add and change queries in
    # dedicated modules
    result: dict[tuple[str, str], Query] = dict()
    for path in query_paths:
        name = path.stem
        loader = importlib.machinery.SourceFileLoader(name, str(path))
        spec = importlib.util.spec_from_loader(name, loader)
        assert spec
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        for variant in dir(module):
            query = getattr(module, variant)
            if isinstance(query, Query):
                result[name, variant] = query
    return result


wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")

for (scenario, variant), query in extract_queries().items():
    if scenario != "full":
        continue
    print('\033[1m', scenario, '\033[0m', variant)

    # Print query to file for inspection
    with open(build_path / f"{scenario}_{variant}.rq", 'w') as f:
        f.write(query.sparql())

    for i, line in enumerate(wfgraph.query(query.sparql()), start=1):
        print(i, line.description)

# result = graph.query("""
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     PREFIX ta: <https://github.com/quangis/transformation-algebra#>
#     PREFIX cct: <https://github.com/quangis/cct#>
#     SELECT ?s WHERE {?s rdf:type ta:Transformation. }
# """)

# for line in result:
#     print(line)

