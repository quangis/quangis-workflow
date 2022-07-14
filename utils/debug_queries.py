#!/usr/bin/env python3
from __future__ import annotations
from rdflib import Graph, Variable  # type: ignore
import csv

from queries import all_queries

wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")


for q in all_queries:
    for variant, query in q["variants"].items():
        if not variant.startswith("eval"):
            continue

        fn = f"{q['name']}_{variant}.csv"

        print()
        print(fn)

        with open(fn, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[Variable("workflow")] + query.steps)

            writer.writeheader()

            # Diagnose how many solutions there are
            num_solutions: dict[Variable, int | None | str] = {}
            for var, count, sparql in query.query_diagnostic(wfgraph):
                print(var)
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
                writer.writerow({k: (v if k != Variable("workflow") else str(v).split("#")[1])
                    for k, v in bindings.items()})
