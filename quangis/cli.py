from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from sys import stderr
from glob import glob
from pathlib import Path
from typing import Iterable, Iterator
from rdflib import Graph, Namespace, URIRef, RDF
from rdflib.util import guess_format

from quangis.tools import Repo
from quangis.workflow import Workflow
from quangis.namespace import CCD, EX, n3
from quangis.polytype import Polytype
from quangis.ccdata import dimensions


def paths(files: Iterable[str]) -> Iterator[Path]:
    # Windows does not natively interpret asterisks as globs
    if platform.system() == 'Windows':
        yield from (Path(globbed) for original in files
            for globbed in glob(original))
    else:
        yield from (Path(f) for f in files)


class CLI(cli.Application):
    """Utilities for the QuAnGIS project"""
    PROGNAME = "quangis"

    def main(self, *args):
        if args:
            print(f"Unknown command {args[0]}")
            return 1
        if not self.nested_command:
            self.help()
            return 1


class WithRepo(object):
    assume_integrity = cli.Flag(["-x", "--assume-integrity"],
        help="disable integrity check for tools file")

    @cli.autoswitch(Path, mandatory=True,
        help="file containing (initial) tool repository")
    def _tools(self, path: Path) -> None:
        self.tools_file = path
        self.tools = Repo.from_file(path,
            check_integrity=not self.assume_integrity)

class WithDestDir(object):
    output_dir = Path(".")

    @cli.switch(["-d", "--destdir"], Path, help="Destination directory")
    def _destination(self, path: Path) -> None:
        if path.is_dir():
            self.output_dir = path
        else:
            raise RuntimeError(f"{path} is not a directory")

@CLI.subcommand("convert-abstract")
class AbstractConverter(cli.Application, WithRepo, WithDestDir):
    """Turn concrete workflows into abstract workflows"""

    def main(self, *WORKFLOW):
        for file in paths(WORKFLOW):
            cwf = Workflow.from_file(file)
            try:
                g = self.tools.convert_to_abstractions(cwf, cwf.root)
            except Exception as e:
                if e.args:
                    print(f"Skipping {file} because of the following "
                        f"{type(e).__name__}: {','.join(e.args)}.", 
                        file=stderr)
                else:
                    print(f"Skipping {file} because of a "
                        f"{type(e).__name__}.")
            else:
                print(f"Successfully processed {file}")
                output_file = self.output_dir / f"{file.stem}_abstract.ttl"
                assert not output_file.exists()
                g.serialize(output_file, format="turtle")
            print()


@CLI.subcommand("synthesis")
class Generator(cli.Application, WithRepo, WithDestDir):
    """Generate workflows using APE"""

    @cli.autoswitch(Path, mandatory=True,
        help="file containing input/output specifications")
    def _config(self, path: Path) -> None:
        g = Graph()
        g.parse(path)
        base = Namespace(path.parent.absolute().as_uri() + "/")
        self.sources: list[list[URIRef]] = [
            list(y for y in g.objects(x, RDF.type) if isinstance(y, URIRef))
            for x in g.objects(None, base.input)]
        self.goals: list[list[URIRef]] = [
            list(y for y in g.objects(x, RDF.type) if isinstance(y, URIRef))
            for x in g.objects(None, base.output)]

    def main(self, *args) -> None:
        from quangis.synthesis import WorkflowGenerator

        gen = WorkflowGenerator(self.tools_file, self.output_dir)

        # To start with, we generate workflows with two inputs and one output, 
        # of which one input is drawn from the following sources, and the other 
        # is the same as the output without the measurement level.
        inputs_outputs: list[tuple[list[Polytype], list[Polytype]]] = []

        # inputs_outputs = [
        #     (
        #         [Polytype.project(dimensions, s) for s in self.sources],
        #         [Polytype.project(dimensions, g) for g in self.goals]
        #     )
        # ]

        for goal_tuple in self.goals:
            goal = Polytype.project(dimensions, goal_tuple)
            source1 = Polytype(goal)
            source1[CCD.NominalA] = {CCD.NominalA}
            for source_tuple in self.sources:
                source2 = Polytype.project(dimensions, source_tuple)
                inputs_outputs.append(([source1, source2], [goal]))

        running_total = 0
        for run, (inputs, outputs) in enumerate(inputs_outputs):
            print(f"Attempting [ {' ] & [ '.join(x.short() for x in inputs)} "
                f"] -> [ {' & '.join(x.short() for x in outputs)} ]")
            for solution in gen.run(inputs, outputs, solutions=1, 
                    prefix=EX.solution):
                running_total += 1
                path = self.output_dir / f"solution{running_total}.ttl"
                print(f"Writing solution: {path}")
                solution.serialize(path, format="ttl")
            print(f"Running total is {running_total}.")

def main():
    CLI.run()


if __name__ == '__main__':
    main()
