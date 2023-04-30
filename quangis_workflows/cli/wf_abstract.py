from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob
from pathlib import Path

from quangis_workflows.repo.tool import ToolRepo
from quangis_workflows.repo.signature import SignatureRepo, \
    update_repositories2
from quangis_workflows.repo.workflow import Workflow


class CLI(cli.Application):
    """This program turns a concrete workflow into one (or more) that refer 
    only to abstract tool signatures."""

    PROGNAME = "quangis-wf-abstract"

    def main(self, *FILE):

        # Windows does not natively interpret asterisks as globs
        if platform.system() == 'Windows':
            FILE = tuple(globbed for original in FILE
                for globbed in glob(original))

        FILE = [Path(f) for f in FILE]

        # TODO as long as the tool repository cannot be read, we just construct 
        # it from the ground up. Should definitely be changed
        sigs = SignatureRepo()
        tools = ToolRepo()
        for file in FILE:
            cwf = Workflow.from_file(file)
            update_repositories2(sigs, tools, cwf)

        sigs.graph().serialize("repo.ttl", format="turtle")
        sigs.graph().serialize("repo.xml", format="xml")

        for file in FILE:
            print(file)
            cwf = Workflow.from_file(file)
            g = sigs.convert_to_signatures(cwf, cwf.root, tools)
            g.serialize(f"{file.stem}_abstract.xml", format="xml")
            g.serialize(f"{file.stem}_abstract.ttl", format="turtle")


def main():
    CLI.run()


if __name__ == '__main__':
    main()
