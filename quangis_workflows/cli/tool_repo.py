from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob

from quangis_workflows.repo.workflow import Workflow
from quangis_workflows.repo.tool import ToolRepo
from quangis_workflows.repo.signature import (SignatureRepo, 
    update_repositories2)


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

        sigs = SignatureRepo()
        tools = ToolRepo()
        for file in FILE:
            cwf = Workflow.from_file(file)
            update_repositories2(sigs, tools, cwf)
        print(sigs.graph().serialize(format="turtle"))
        print(tools.graph().serialize(format="turtle"))

        # repo.graph().serialize("repo.ttl", format="turtle")
        # repo.graph().serialize("repo.xml", format="xml")


def main():
    CLI.run()


if __name__ == '__main__':
    main()
