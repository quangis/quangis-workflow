#!/usr/bin/env python3
from __future__ import annotations
from rdflib import Graph, Variable  # type: ignore
import sys
import csv

import config  # type: ignore
from queries import all_queries

wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")


for q in all_queries:
    for variant, query in q["variants"].items():
        if not variant.startswith("eval"):
            continue

        print()
        print(q["name"], variant)

        # with open(sys.stdout, 'w', newline='') as csvfile:
        writer = csv.DictWriter(sys.stdout, fieldnames=query.steps)

        writer.writeheader()

        # Diagnose how many solutions there are
        num_solutions: dict[Variable, int | None | str] = {}
        for var, count, sparql in query.query_diagnostic(wfgraph):
            num_solutions[var] = count

        # Find the last non-failed step
        selection: Variable | None = None
        for step in reversed(query.steps):
            if num_solutions.get(step):
                selection = step
                break

        num_solutions[selection] = f"{num_solutions[selection]}*"

        writer.writerow(num_solutions)

        for bindings in query.query_step_bindings(wfgraph, at_step=selection):
            writer.writerow(bindings)
