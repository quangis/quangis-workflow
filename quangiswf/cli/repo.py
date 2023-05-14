from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob
from pathlib import Path
from typing import Iterable, Iterator

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
    repo = cli.SwitchAttr(["--repo"],
        help="RDF file containing tools, supertools and signatures",
        argtype=Repo.from_file,
        mandatory=True)


@CLI.subcommand("construct")
class Constructor(cli.Application, WithRepo):
    """Extract a tool repository from concrete workflows"""

    def main(self, *FILE):
        for file in paths(FILE):
            cwf = Workflow.from_file(file)
            self.repo.update(cwf)
        print(self.repo.graph().serialize(format="turtle"))

        # repo.graph().serialize("repo.ttl", format="turtle")
        # repo.graph().serialize("repo.xml", format="xml")


@CLI.subcommand("convert")
class Converter(cli.Application, WithRepo):
    """Turn concrete workflows into abstract workflows"""

    def main(self, *FILE):
        for file in paths(FILE):
            try:
                cwf = Workflow.from_file(file)
                # self.repo.update(cwf)
                g = self.repo.convert_to_signatures(cwf, cwf.root)
                g.serialize(f"{file.stem}_abstract.ttl", format="turtle")

            except Exception as e:
                print(f"Skipping {file} because of the following "
                    f"{type(e).__name__}: {e}")
            else:
                print(f"Successfully processed {file}")

        self.repo.graph().serialize("repo.ttl", format="turtle")


def main():
    CLI.run()


if __name__ == '__main__':
    main()
