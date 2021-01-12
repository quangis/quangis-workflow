"""
Various utility functions.
"""

import os
import os.path
import urllib.request
import logging


def download_if_missing(path, url):
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.mkdir(directory)

    if not os.path.isfile(path):
        logging.warning(
            "{} not found; now downloading from {}".format(path, url))
        urllib.request.urlretrieve(url, filename=path)

    return path
