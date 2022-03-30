#!/usr/bin/env python3

from __future__ import annotations

from sys import stderr
import json
import csv
from rdflib import Graph  # type: ignore
from rdflib.term import Node  # type: ignore
from plumbum import cli  # type: ignore
from transformation_algebra import Query, TransformationGraph

from config import REPO  # type: ignore
from workflow import Workflow  # type: ignore
from cct import cct


class Utility(cli.Application):
    def main(self, *args):
        if args:
            print(f"Unknown command {args[0]}")
            return 1
        if not self.nested_command:
            self.helpall()
            return 1


@Utility.subcommand("vocab")
class VocabBuilder(cli.Application):
    "Build CCT vocabulary file."

    @cli.positional(cli.NonexistentPath)
    def main(self, output):
        vocab = TransformationGraph(cct)
        vocab.add_vocabulary()
        vocab.serialize(str(output), format='ttl', encoding='utf-8')


@Utility.subcommand("graph")
class TransformationGraphBuilder(cli.Application):
    """
    Generate transformation graphs for entire workflows, concatenating the
    algebra expressions for each individual use of a tool.
    """
    no_passthrough = cli.Flag("--no-passthrough", default=False,
        help="Treat tools as insular, disregarding specific input types")

    @cli.positional(cli.ExistingFile, cli.NonexistentPath)
    def main(self, wf_path, output):
        wf = Workflow(wf_path)
        g = TransformationGraph(cct, with_noncanonical_types=False,
            passthrough=not self.no_passthrough)
        g.add_workflow(wf.root, wf.wf, wf.sources)
        g.serialize(str(output), format='ttl', encoding='utf-8')


@Utility.subcommand("query")
class QueryRunner(cli.Application):
    "Run a query."
    output = cli.SwitchAttr(["-o", "--output"], cli.NonexistentPath,
        mandatory=True, help="Output CSV file")
    blackbox = cli.Flag("--blackbox", help="Only consider input and output")
    unordered = cli.Flag("--unordered", help="Disregard stated chronology")

    @cli.positional(cli.ExistingFile)
    def main(self, *QUERY_FILE):
        if not QUERY_FILE:
            self.help()
            return 1
        else:
            wfgraph = Graph(store='SPARQLStore')
            wfgraph.open("http://localhost:3030/name")

            opts = {"by_input": True, "by_output": True, "by_operators": False}
            opts["by_chronology"] = not self.unordered and not self.blackbox
            opts["by_types"] = not self.blackbox

            queries: list[tuple[str, set[Node], Query]] = []
            all_workflows: set[Node] = set()
            for path in QUERY_FILE:
                with open(path, 'r') as fp:
                    dct = json.load(fp)
                query = Query.from_dict(cct, dct)
                expected = set(REPO[e] for e in dct["expected"])
                all_workflows.update(expected)
                queries.append((path.stem, expected, query))

            header = ["Query", "Precision", "Recall"] + sorted([
                str(wf)[len(REPO):] for wf in all_workflows])

            with open(self.output, 'w', newline='') as h:
                w = csv.DictWriter(h, fieldnames=header)
                w.writeheader()
                n_tpos = 0
                n_tneg = 0
                n_fpos = 0
                n_fneg = 0
                for name, expected, query in queries:
                    sparql = query.sparql(**opts)
                    result: dict[str, str] = {"Query": name}
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

                        result[str(wf)[len(REPO):]] = s

                    false_pos = (pos - expected)
                    false_neg = (expected - pos)
                    true_pos = (pos - false_pos)
                    true_neg = (set(all_workflows) - true_pos)

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

                try:
                    w.writerow({
                        "Precision": "{0:.3f}".format(n_tpos / (n_tpos + n_fpos)),
                        "Recall": "{0:.3f}".format(n_tpos / (n_tpos + n_fneg))
                    })
                except ZeroDivisionError:
                    w.writerow({
                        "Precision": "{0:.3f}".format(0),
                        "Recall": "{0:.3f}".format(0)
                    })


if __name__ == '__main__':
    Utility.run()
