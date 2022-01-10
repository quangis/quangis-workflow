#!/usr/bin/env python3
"""
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
from rdflib import Graph  # type: ignore
from transformation_algebra.query import Query
from typing import Iterator
from rdflib.term import Node

from config import query_paths, build_path  # type: ignore


def extract_queries() -> Iterator[tuple[str, str, set[Node], Query]]:
    """
    Extract queries defined in modules.
    """
    # Perhaps overengineered but makes it simple to add and change queries in
    # dedicated modules
    for path in query_paths:
        name = path.stem
        loader = importlib.machinery.SourceFileLoader(name, str(path))
        spec = importlib.util.spec_from_loader(name, loader)
        assert spec
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)

        workflows = getattr(module, 'workflows')
        for variant in dir(module):
            query = getattr(module, variant)
            if isinstance(query, Query):
                yield name, variant, workflows, query


def result(actual: set, expected: set,
        correct=lambda x: f"\033[32m{x}\033[0m",
        wrong=lambda x: f"\033[31m{x}\033[0m",
        empty='none') -> str:
    """
    Stylize the contents of a set depending on whether its elements should be
    there or not.
    """
    if actual:
        return ", ".join(correct(r) if r in expected else wrong(r)
            for r in actual)
    else:
        return (correct if not expected else wrong)(empty)


wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")

# Varying options to try
option_variants = {
    "order": {"by_types": True, "by_order": True},
    "justtypes": {"by_types": True, "by_order": False}
}
for scenario, variant, expected_workflows, query in extract_queries():
    if variant != "query":
        continue

    for optname, options in option_variants.items():

        query2 = Query(query.language, query.flow, **options)

        print(f'\033[1m\033[4m{scenario}\033[0m', variant, optname)

        # Print query to file for inspection
        path = build_path / f"{scenario}_{variant}_{optname}.rq"
        # print("Building", path.name)
        with open(path, 'w') as f:
            f.write(query2.sparql())

        # Run the query
        try:
            results = wfgraph.query(query2.sparql())
            positives = set(r.workflow for r in results)

            false_pos = (positives - expected_workflows)
            false_neg = (expected_workflows - positives)
            correct = positives - false_pos - false_neg

            print("Correct:", result(correct, expected_workflows))
            print("False positives:", result(false_pos, set()))
            print("Missing:", result(false_neg, set()))

        except ValueError:
            print("Not firing queries, since the server is down.")

        print()
