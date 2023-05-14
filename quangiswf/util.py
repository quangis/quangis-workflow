"""
Various utility functions.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
root_dir = Path(__file__).parent.parent


def download(url: str, dest_dir: Path | None = None,
        name: str | None = None) -> Path:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """
    if not dest_dir:
        dest_dir = root_dir
    if not name:
        name = Path(url).name

    assert isinstance(dest_dir, Path)
    path = dest_dir / name
    dest_dir.mkdir(exist_ok=True)
    if not path.exists():
        print(f"{path} not found; now downloading from {url}")
        urllib.request.urlretrieve(url, filename=path)

    return path
