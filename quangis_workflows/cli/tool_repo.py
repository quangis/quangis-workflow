from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob

from quangis_workflows.tool_repo import (
    ConcreteWorkflow, ToolRepository)


class CLI(cli.Application):
    """
    This tool generates an abstract tool repository by analyzing given concrete 
    workflows.
    """

    PROGNAME = "quangis-tool-repo"

    def main(self, *FILE):

        # Windows does not natively interpret asterisks as globs
        if platform.system() == 'Windows':
            FILE = tuple(globbed for original in FILE
                for globbed in glob(original))

        repo = ToolRepository()
        for file in FILE:
            cwf = ConcreteWorkflow.from_file(file)
            repo.collect(cwf)
        print(repo.graph().serialize(format="turtle"))


def main():
    CLI.run()


if __name__ == '__main__':
    main()
