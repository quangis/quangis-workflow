from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob

from quangis_workflows.repo.workflow import Workflow
from quangis_workflows.repo.repo import Repo


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

        repo = Repo()
        for file in FILE:
            cwf = Workflow.from_file(file)
            repo.update(cwf)
        print(repo.graph().serialize(format="turtle"))

        # repo.graph().serialize("repo.ttl", format="turtle")
        # repo.graph().serialize("repo.xml", format="xml")


def main():
    CLI.run()


if __name__ == '__main__':
    main()
