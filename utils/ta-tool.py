#!/usr/bin/env python3

from __future__ import annotations

import csv
from rdflib import Graph  # type: ignore
from rdflib.term import Node, Literal  # type: ignore
from rdflib.namespace import RDFS  # type: ignore
from rdflib.tools.rdf2dot import rdf2dot  # type: ignore
from plumbum import cli  # type: ignore
from itertools import chain
from transformation_algebra import TransformationQuery, TransformationGraph, TA
from typing import NamedTuple, Iterable

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
    format = cli.SwitchAttr(["-f", "--format"], cli.Set("rdf", "ttl", "json-ld"),
        default="ttl")

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
            vocab.serialize(str(output), format=self.format, encoding='utf-8')


@Tatool.subcommand("graph")
class TransformationGraphBuilder(cli.Application):
    """
    Generate transformation graphs for entire workflows, concatenating the
    algebra expressions for each individual use of a tool
    """
    visual = cli.Flag("--visual", default=False)
    format = cli.SwitchAttr(["-f", "--format"], cli.Set("rdf", "ttl", "json-ld"),
        default="ttl")
    blocked = cli.Flag(["--blocked"], default=False,
        help="Do not pass output type of one tool to the next")
    opaque = cli.Flag(["--opaque"], default=False,
        help="Do not annotate types internal to the tools")

    @cli.positional(cli.ExistingFile, cli.NonexistentPath)
    def main(self, wf_path, output_path):
        wf = Workflow(wf_path)
        if self.visual:
            g = TransformationGraph(cct, minimal=True, with_labels=True,
                with_intermediate_types=not self.opaque,
                passthrough=not self.blocked)
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
                passthrough=not self.blocked,
                with_intermediate_types=not self.opaque)
            g.add_workflow(wf.root, wf.wf, wf.sources)
            g.serialize(str(output_path), format=self.format, encoding='utf-8')


class Task(NamedTuple):
    name: str
    query: TransformationQuery
    expected: set[Node]
    actual: set[Node]


def graph(url: str) -> Graph:
    g = Graph(store='SPARQLStore')
    g.open(url)
    return g


@Tatool.subcommand("query")
class QueryRunner(cli.Application):
    """
    Run transformation queries against a SPARQL endpoint. If no endpoint is
    given, just output the query instead.
    """

    output = cli.SwitchAttr(["-o", "--output"], cli.NonexistentPath,
        mandatory=True, help="Output file")
    format = cli.SwitchAttr(["-f", "--format"], cli.Set("sparql", "csv"),
        default="csv", help="Output format")
    chronological = cli.Flag(["-c", "--chronological"],
        default=False, help="Take into account order")
    blackbox = cli.Flag(["-b", "--blackbox"],
        default=False, help="Only consider input and output of the workflows")
    endpoint = cli.SwitchAttr(["-e", "--endpoint"], argtype=graph,
        help="SPARQL endpoint to send queries to")

    def evaluate(self, path, **opts) -> Task:
        """
        Parse and run a single task.
        """
        graph = TransformationGraph.from_rdf(path, cct)
        query = TransformationQuery(cct, graph, **opts)
        return Task(name=path.stem, query=query,
            expected=set(graph.objects(query.root, TA.implementation)),
            actual=(query.run(self.endpoint) if self.endpoint else set()))

    def summarize(self, tasks: Iterable[Task]) -> None:
        """
        Write a CSV summary of the tasks to the output.
        """

        workflows = set.union(*chain(
            (t.actual for t in tasks),
            (t.expected for t in tasks)))

        header = ["Task", "Precision", "Recall"] + sorted([
            str(wf)[len(REPO):] for wf in workflows])

        with open(self.output, 'w', newline='') as h:
            n_tpos, n_tneg, n_fpos, n_fneg = 0, 0, 0, 0
            w = csv.DictWriter(h, fieldnames=header)
            w.writeheader()
            for task in tasks:
                result: dict[str, str] = {"Task": task.name}
                expected, actual = task.expected, task.actual
                for wf in workflows:
                    s = "●" if wf in actual else "○"
                    if not expected:
                        s += "?"
                    elif (wf in actual) ^ (wf in expected):
                        s += "⨯"
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
                w.writerow({"Precision": "?", "Recall": "?"})

    @cli.positional(cli.ExistingFile)
    def main(self, *QUERY_FILE):
        if not QUERY_FILE:
            self.help()
            return 1
        else:
            # Parse tasks and optionally run associated queries
            tasks = [self.evaluate(task_file, by_io=True,
                by_operators=False, by_types=not self.blackbox,
                by_chronology=self.chronological and not self.blackbox,
            ) for task_file in QUERY_FILE]

            # Summarize query results
            if self.format == "sparql":
                with open(self.output, 'w', newline='') as h:
                    h.write("---\n")
                    for task in tasks:
                        h.write(task.query.sparql())
                        h.write("\n\nActual: ")
                        h.write(", ".join(t.n3() for t in task.actual))
                        h.write("\nExpected: ")
                        h.write(", ".join(t.n3() for t in task.expected))
                        h.write("\n---\n")
            else:
                assert self.format == "csv"
                self.summarize(tasks)


if __name__ == '__main__':
    Tatool.run()
