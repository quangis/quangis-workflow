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
    "inputs": {"by_input": True, "by_output": False, "by_operators": False, "by_types": False, "by_chronology": False},
    # "output": {"by_operators": False, "by_types": False, "by_chronology": False},
    # "types": {"by_operators": False, "by_types": True, "by_chronology": False},
    # "ordered": {"by_operators": False, "by_types": True, "by_chronology": True}
}


def wfname(wf: Node) -> str:
    return str(wf)[len(REPO):]


header = ["Scenario", "Variant", "Options", "Precision", "Recall"] + sorted([
    wfname(wf) for wf in all_workflows])

with open(build_path / "results.csv", 'w', newline='') as f:

    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()

    for optname, options in option_variants.items():

        n_tpos = 0
        n_tneg = 0
        n_fpos = 0
        n_fneg = 0

        # for scenario, variant, expected_workflows, query in all_queries:
        for elem in all_queries:
            scenario = elem["name"]
            expected = set(elem["expected"])
            for variant, query in elem["variants"].items():

                if not variant.startswith("eval"):
                    continue

                result: dict[str, str | float] = {
                    "Scenario": scenario,
                    "Variant": variant,
                    "Options": optname,
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
                except ValueError:
                    print("Server is down or timed out.")
                    pos = set()
                else:
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

                false_pos = (pos - expected)
                false_neg = (expected - pos)
                true_pos = (pos - false_pos)
                true_neg = (set(all_workflows) - true_pos)
                correct = pos - false_pos - false_neg

                n_tpos += (i_tpos := len(true_pos))
                n_tneg += (i_tneg := len(true_neg))
                n_fpos += (i_fpos := len(false_pos))
                n_fneg += (i_fneg := len(false_neg))

                try:
                    result["Precision"] = "{0:.3f}".format(
                        i_tpos / (i_tpos + i_fpos))
                except ZeroDivisionError:
                    result["Precision"] = "0.000"

                try:
                    result["Recall"] = "{0:.3f}".format(
                        i_tpos / (i_tpos + i_fneg))
                except ZeroDivisionError:
                    result["Recall"] = "0.000"

                w.writerow(result)

                print("Correct:", correct)
                print("False positives:", false_pos)
                print("Missing:", false_neg)
                print()

        w.writerow({
            "Scenario": "Total",
            "Options": optname,
            "Precision": "{0:.3f}".format(n_tpos / (n_tpos + n_fpos)),
            "Recall": "{0:.3f}".format(n_tpos / (n_tpos + n_fneg))
        })

