from __future__ import annotations
from plumbum import cli  # type: ignore
import platform
from glob import glob
from pathlib import Path

from quangiswf.repo.repo import Repo
from quangiswf.repo.workflow import Workflow


class CLI(cli.Application):
    """This program turns a concrete workflow into one (or more) that refer 
    only to abstract tool signatures."""

    PROGNAME = "quangiswf-conv"

    def main(self, *FILE):

        # Windows does not natively interpret asterisks as globs
        if platform.system() == 'Windows':
            FILE = tuple(globbed for original in FILE
                for globbed in glob(original))

        FILE = [Path(f) for f in FILE]

        # TODO as long as the tool repository cannot be read, we just construct 
        # it from the ground up. Should definitely be changed
        repo = Repo()
        for file in FILE:
            try:
                cwf = Workflow.from_file(file)
                repo.update(cwf)
                g = repo.convert_to_signatures(cwf, cwf.root)
                g.serialize(f"{file.stem}_abstract.ttl", format="turtle")

            except Exception as e:
                print(f"Skipping {file} because of the following "
                    f"{type(e).__name__}: {e}")
            else:
                print(f"Successfully processed {file}")

        repo.graph().serialize("repo.ttl", format="turtle")

def main():
    CLI.run()


if __name__ == '__main__':
    main()
