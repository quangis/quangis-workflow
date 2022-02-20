#!/usr/bin/env python3
"""
"""

# https://openpyxl.readthedocs.io/en/stable/usage.html#write-a-workbook
# Query Variant Options {Workflows}
# ?     ?       ?       1 1 0 1 1

from __future__ import annotations

from rdflib import Graph  # type: ignore
from rdflib.term import Node  # type: ignore
import csv

from config import build_path, REPO  # type: ignore

from queries import all_queries, all_workflows


wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")

# Varying options to try
option_variants = {
    "ordered": {"by_types": True, "by_chronology": True},
    "types": {"by_types": True, "by_chronology": False}
}


def wfname(wf: Node) -> str:
    return str(wf)[len(REPO):]


header = ["Scenario", "Variant", "Options"] + sorted([
    wfname(wf) for wf in all_workflows])

with open(build_path / "results.csv", 'w', newline='') as f:

    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()

    # for scenario, variant, expected_workflows, query in all_queries:
    for elem in all_queries:
        scenario = elem["name"]
        expected = set(elem["expected"])
        for variant, query in elem["variants"].items():

            if not variant.startswith("eval"):
                continue

            for optname, options in option_variants.items():

                result: dict[str, str] = {
                    "Scenario": scenario,
                    "Variant": variant,
                    "Options": optname
                }

                print(f'\033[1m\033[4m{scenario}\033[0m', variant, optname)

                sparql = query.sparql(**options)

                # Print query to file for inspection
                path = build_path / f"{scenario}_{variant}_{optname}.rq"
                # print("Building", path.name)
                with open(path, 'w') as f:
                    f.write(sparql)

                # Run the query
                try:
                    results = wfgraph.query(sparql)
                    pos = set(r.workflow for r in results)

                    for wf in all_workflows:
                        if wf in pos:
                            if wf in expected:
                                s = "TP"
                            else:
                                s = "FP"
                        else:
                            if wf in expected:
                                s = "FN"
                            else:
                                s = "TN"

                        result[wfname(wf)] = s

                    w.writerow(result)

                    # Write to terminal
                    false_pos = (pos - expected)
                    false_neg = (expected - pos)
                    correct = pos - false_pos - false_neg

                    print("Correct:", correct)
                    print("False positives:", false_pos)
                    print("Missing:", false_neg)

                except ValueError:
                    print("Not firing queries, since the server is down or timed out.")

                print()
