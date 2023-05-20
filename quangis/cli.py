from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob
from pathlib import Path
from typing import Iterable, Iterator
from rdflib import Graph, Namespace, URIRef, RDF
from rdflib.util import guess_format

from quangis.tools import Repo
from quangis.workflow import Workflow
from quangis.namespace import CCD, EX
from quangis.polytype import Polytype


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

@CLI.subcommand("update-tools")
class RepoBuilder(cli.Application, WithRepo, WithDestDir):
    """Extract a tool repository from concrete workflows"""

    output_file = cli.SwitchAttr(["-o", "--output"],
        help="output file", default=None)

    def main(self, *WORKFLOW):
        repo = self.tools
        for file in paths(WORKFLOW):
            cwf = Workflow.from_file(file)
            repo.update(cwf)

        graph = repo.graph()
        if self.output_file:
            graph.serialize(self.output_file,
                format=guess_format(self.output_file))
        else:
            print(graph.serialize(format="turtle"))


@CLI.subcommand("convert-abstract")
class AbstractConverter(cli.Application, WithRepo, WithDestDir):
    """Turn concrete workflows into abstract workflows"""

    def main(self, *WORKFLOW):
        for file in paths(WORKFLOW):
            cwf = Workflow.from_file(file)
            try:
                # self.repo.update(cwf)
                g = self.tools.convert_to_signatures(cwf, cwf.root)
            except Exception as e:
                print(f"Skipping {file} because of the following "
                    f"{type(e).__name__}: {e}")
            else:
                print(f"Successfully processed {file}")
                assert self.output_dir.isdir()
                output_file = self.output_dir / f"{file.stem}_abstract.ttl"
                assert not self.output_file.exists()
                g.serialize(output_file, format="turtle")


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
        inputs_outputs: list[tuple[str, list[Polytype], list[Polytype]]] = []
        for goal_tuple in self.goals:
            goal = Polytype(gen.dimensions, goal_tuple)
            source1 = Polytype(goal)
            source1[CCD.NominalA] = {CCD.NominalA}
            for source_tuple in self.sources:
                source2 = Polytype(gen.dimensions, source_tuple)
                inputs_outputs.append((
                    f"{source1.short()}+{source2.short()}_{goal.short()}_",
                    [source1, source2], [goal]))

        running_total = 0
        for run, (name, inputs, outputs) in enumerate(inputs_outputs):
            for solution in gen.run(inputs, outputs, solutions=1, 
                    prefix=EX[name]):
                running_total += 1
                path = self.output_dir / f"solution{running_total}.ttl"
                print(f"Writing solution: {path}")
                solution.serialize(path, format="ttl")

def main():
    CLI.run()


if __name__ == '__main__':
    main()
