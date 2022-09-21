"""
Functions to deal with application data.
"""

import sys
import urllib
from os import getenv
from pathlib import Path
from typing import Optional


def data_dir() -> Path:
    """
    Get the path to the directory where we store application-specific data
    files.
    """

    if sys.platform.startswith("win"):
        path = Path(getenv("LOCALAPPDATA"))
    elif sys.platform.startswith("darwin"):
        path = Path("~/Library/Application Support")
    elif sys.platform.startswith("linux"):
        path = Path(getenv("XDG_DATA_HOME", "~/.local/share"))
    else:
        raise RuntimeError("Unsupported platform")

    path = Path(path).expanduser() / "apey"

    try:
        path.mkdir(parents=True)
    except FileExistsError:
        pass

    return path


def get(filename: str, url: Optional[str] = None) -> Path:
    """
    Get a data file, or download it if it is not present. Returns path to the
    file.
    """

    path = data_dir() / filename

    if not path.exists():
        if url:
            print(
                f"Could not find data file {path}; now downloading from {url}",
                file=sys.stderr)
            urllib.request.urlretrieve(url, filename=path)
        else:
            raise FileNotFoundError

    return path
