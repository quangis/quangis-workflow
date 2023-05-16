from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob
from pathlib import Path
from typing import Iterable, Iterator
from rdflib.util import guess_format

from quangiswf.repo.repo import Repo
from quangiswf.repo.workflow import Workflow


def paths(files: Iterable[str]) -> Iterator[Path]:
    # Windows does not natively interpret asterisks as globs
    if platform.system() == 'Windows':
        yield from (Path(globbed) for original in files
            for globbed in glob(original))
    else:
        yield from (Path(f) for f in files)


class CLI(cli.Application):

    PROGNAME = "quangiswf-repo"

    def main(self, *args):
        if args:
            print(f"Unknown command {args[0]}")
            return 1
        if not self.nested_command:
            self.help()
            return 1


class WithRepo(object):
    repo = cli.SwitchAttr(["--tools"],
        help="abstract tools, concrete tools and supertools",
        argtype=lambda x: Repo.from_file(x, check_integrity=True),
        mandatory=True)


@CLI.subcommand("construct")
class Constructor(cli.Application, WithRepo):
    """Extract a tool repository from concrete workflows"""

    output_file = cli.SwitchAttr(["-o", "--output"],
        help="output file", default=None)

    def main(self, *FILE):
        repo = self.repo
        for file in paths(FILE):
            cwf = Workflow.from_file(file)
            repo.update(cwf)

        graph = repo.graph()
        if self.output_file:
            graph.serialize(self.output_file,
                format=guess_format(self.output_file))
        else:
            print(graph.serialize(format="turtle"))


@CLI.subcommand("convert")
class Converter(cli.Application, WithRepo):
    """Turn concrete workflows into abstract workflows"""

    output_dir = cli.SwitchAttr(["-d", "--destdir"],
        help="output directory",
        default=Path("."))

    def main(self, *FILE):
        for file in paths(FILE):
            cwf = Workflow.from_file(file)
            try:
                # self.repo.update(cwf)
                g = self.repo.convert_to_signatures(cwf, cwf.root)
            except Exception as e:
                print(f"Skipping {file} because of the following "
                    f"{type(e).__name__}: {e}")
            else:
                print(f"Successfully processed {file}")
                assert self.output_dir.isdir()
                output_file = self.output_dir / f"{file.stem}_abstract.ttl"
                assert not self.output_file.exists()
                g.serialize(output_file, format="turtle")


def main():
    CLI.run()


if __name__ == '__main__':
    main()
