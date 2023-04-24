from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob

from quangis_workflows.tool_repo import (
    ConcreteWorkflow, ToolRepository)


class CLI(cli.Application):
    """This program turns a concrete workflow into one (or more) that refer 
    only to abstract tool signatures."""

    PROGNAME = "quangis-wf-abstract"

    def main(self, *FILE):

        # Windows does not natively interpret asterisks as globs
        if platform.system() == 'Windows':
            FILE = tuple(globbed for original in FILE
                for globbed in glob(original))

        # TODO as long as the tool repository cannot be read, we just construct 
        # it from the ground up. Should definitely be changed
        repo = ToolRepository()
        for file in FILE:
            cwf = ConcreteWorkflow.from_file(file)
            repo.collect(cwf)

        for file in FILE:
            print(file)
            cwf = ConcreteWorkflow.from_file(file)
            g = cwf.abstraction(cwf.root, repo)
            print(g.serialize(format="turtle"))


def main():
    CLI.run()


if __name__ == '__main__':
    main()
