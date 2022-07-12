#!/usr/bin/env python3

from __future__ import annotations

import csv
from rdflib import Graph  # type: ignore
from rdflib.term import Node, Literal  # type: ignore
from rdflib.namespace import RDFS  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from plumbum import cli  # type: ignore
from transformation_algebra import TransformationQuery, TransformationGraph, TA
from typing import NamedTuple

from config import REPO, TOOLS  # type: ignore
from workflow import Workflow  # type: ignore
from cct import cct


class Tatool(cli.Application):
    """
    A utility to create RDFs, graph visualizations, queries and other files
    relevant to workflows annotated with tool descriptions from the CCT
    algebra
    """

    def main(self, *args):
        if args:
            print(f"Unknown command {args[0]}")
            return 1
        if not self.nested_command:
            self.help()
            return 1


@Tatool.subcommand("merge")
class Merger(cli.Application):
    """
    Merge RDF graphs
    """

    @cli.positional(cli.NonexistentPath, cli.ExistingFile)
    def main(self, output, *inputs):
        g = Graph()
        for i in inputs:
            g.parse(str(i))
        g.serialize(str(output), format='ttl', encoding='utf-8')


@Tatool.subcommand("vocab")
class VocabBuilder(cli.Application):
    "Build CCT vocabulary file"
    visual = cli.Flag("--visual", default=False)

    @cli.positional(cli.NonexistentPath)
    def main(self, output):
        if self.visual:
            vocab = TransformationGraph(cct, minimal=True, with_labels=True)
            vocab.add_taxonomy()
            with open(output, 'w') as f:
                rdf2dot(vocab, f)
        else:
            vocab = TransformationGraph(cct)
            vocab.add_vocabulary()
            vocab.serialize(str(output), format='ttl', encoding='utf-8')


@Tatool.subcommand("graph")
class TransformationGraphBuilder(cli.Application):
    """
    Generate transformation graphs for entire workflows, concatenating the
    algebra expressions for each individual use of a tool
    """
    visual = cli.Flag("--visual", default=False)

    passthrough = True

    @cli.switch(["-p", "--passthrough"], cli.Set("pass", "block"),
        help="Whether to pass output type of one tool to the next")
    def _passthrough(self, value):
        self.passthrough = (value != "block")

    internals = True

    @cli.switch(["-i", "--internal"], cli.Set("opaque", "transparent"),
        help="Either treat tools as black boxes, or annotate their internals")
    def _internals(self, value):
        self.internals = (value != "opaque")

    @cli.positional(cli.ExistingFile, cli.NonexistentPath)
    def main(self, wf_path, output_path):
        wf = Workflow(wf_path)
        if self.visual:
            g = TransformationGraph(cct, minimal=True, with_labels=True,
                with_intermediate_types=self.internals,
                passthrough=self.passthrough)
            step2expr = g.add_workflow(wf.root, wf.wf, wf.sources)

            # Annotate the expression nodes that correspond with output nodes
            # of a tool with said tool
            for output, tool in wf.tools.items():
                g.add((step2expr[output], RDFS.comment, Literal(
                    "using " + tool[len(TOOLS):]
                )))
            for output, comment in wf.comment.items():
                g.add((step2expr[output], RDFS.comment, Literal(comment)))

            g.add((step2expr[wf.output], RDFS.comment, Literal("output")))

            with open(output_path, 'w') as f:
                rdf2dot(g, f)
        else:
            g = TransformationGraph(cct, with_noncanonical_types=False,
                passthrough=self.passthrough,
                with_intermediate_types=self.internals)
            g.add_workflow(wf.root, wf.wf, wf.sources)
            g.serialize(str(output_path), format='ttl', encoding='utf-8')


class Task(NamedTuple):
    name: str
    query: TransformationQuery
    expected: set[Node]
    actual: set[Node]


@Tatool.subcommand("query")
class QueryRunner(cli.Application):
    """
    Run transformation queries against a SPARQL endpoint. If no endpoint is
    given, just output the query instead.
    """

    output = cli.SwitchAttr(["-o", "--output"], cli.NonexistentPath,
        mandatory=True, help="Output file")
    endpoint = cli.SwitchAttr(["-e", "--endpoint"],
        help="SPARQL endpoint; if none is given, output queries; otherwise "
             "output results in CSV format")

    blackbox = cli.Flag("--blackbox", help="Only consider input and output",
        default=False)

    ordered = True

    @cli.switch(["--order"], cli.Set("chronological", "any"),
        help="Whether to take into account order")
    def _ordered(self, value):
        self.ordered = (value == "chronological")

    @cli.positional(cli.ExistingFile)
    def main(self, *QUERY_FILE):
        if not QUERY_FILE:
            self.help()
            return 1
        else:
            # Determine whether there is an endpoint to send queries to
            if self.endpoint:
                wfgraph = Graph(store='SPARQLStore')
                wfgraph.open(self.endpoint)
            else:
                wfgraph = None

            # Determine options
            opts = {"by_io": True, "by_operators": False}
            opts["by_chronology"] = self.ordered and not self.blackbox
            opts["by_types"] = not self.blackbox

            tasks: list[Task] = []
            workflows: set[Node] = set()
            for path in QUERY_FILE:
                name = path.stem
                graph = TransformationGraph.from_rdf(path, cct)
                query = TransformationQuery(cct, graph, **opts)

                expected = set(query.graph.objects(query.root,
                    TA.implementation))
                actual = query.run(wfgraph) if wfgraph else set()

                workflows.update(expected)
                workflows.update(actual)
                tasks.append(Task(name, query, expected, actual))

            header = ["Task", "Precision", "Recall"] + sorted([
                str(wf)[len(REPO):] for wf in workflows])

            # Create and optionally send queries
            if not wfgraph:
                with open(self.output, 'w', newline='') as h:
                    for task in tasks:
                        h.write(task.query.sparql())
            else:
                with open(self.output, 'w', newline='') as h:
                    w = csv.DictWriter(h, fieldnames=header)
                    w.writeheader()
                    n_tpos, n_tneg, n_fpos, n_fneg = 0, 0, 0, 0
                    for task in tasks:
                        result: dict[str, str] = {"Task": task.name}
                        expected, actual = task.expected, task.actual

                        for wf in workflows:
                            if wf in actual:
                                if not expected:
                                    s = "●?"  # positive
                                elif wf in expected:
                                    s = "● "  # true positive
                                else:
                                    s = "●⨯"  # false positive
                            else:
                                if not expected:
                                    s = "○?"  # negative
                                if wf in expected:
                                    s = "○⨯"  # false negative
                                else:
                                    s = "○ "  # true negative

                            result[str(wf)[len(REPO):]] = s

                        n_fpos += len(actual - expected)
                        n_fneg += len(expected - actual)
                        n_tpos += len(actual.intersection(expected))
                        n_tneg += len(workflows - expected - actual)
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
    Tatool.run()
