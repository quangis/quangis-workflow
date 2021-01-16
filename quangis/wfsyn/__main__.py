#!/usr/bin/env python3
"""
A workflow generator: a wrapper for APE that generates input data from a given
OWL data ontology and a given tool annotation file, by projecting classes to
ontology dimensions.

When run on its own, this is a command-line interface to the APE wrapper.
"""

import os.path
import argparse
import logging
import urllib.request
from importlib import reload

from quangis.wfsyn import wfsyn
from quangis.ontology import Ontology
from quangis.namespace import CCD
from quangis.semtype import SemType
from quangis.utils import uri, shorten


def download_if_missing(path: str, url: str) -> str:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.mkdir(directory)

    if not os.path.isfile(path):
        logging.warning(
            "{} not found; now downloading from {}".format(path, url))
        urllib.request.urlretrieve(url, filename=path)

    return path


parser = argparse.ArgumentParser(
    description="Wrapper for APE that synthesises CCD workflows"
)

parser.add_argument(
    '--types',
    help="core concept datatype ontology in RDF")

parser.add_argument(
    '--tools',
    help="tool annotation ontology in RDF")

parser.add_argument(
    '-d', '--dimension',
    nargs='+',
    type=uri,
    default=[CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA],
    help="semantic dimensions")

parser.add_argument(
    '-n', '--solutions',
    type=int,
    default=5,
    help="number of solution workflows attempted of find")

parser.add_argument(
    '--log',
    choices=['debug', 'info', 'warning', 'error', 'critical'],
    default='info',
    help="Level of information logged to the terminal")

args = parser.parse_args()

# To force logging on this package; TODO prettier solution
reload(logging)
logging.basicConfig(
    level=getattr(logging, args.log.upper()),
    format="\033[1m%(levelname)s \033[0m%(message)s",
)

if not args.types:
    args.types = download_if_missing(
       path="CoreConceptData.rdf",
       url="http://geographicknowledge.de/vocab/CoreConceptData.rdf"
    )

if not args.tools:
    args.tools = download_if_missing(
        path="ToolDescription.ttl",
        url="https://raw.githubusercontent.com/simonscheider/"
            "QuAnGIS/master/ToolRepository/ToolDescription.ttl"
    )

logging.info("Dimensions: {}".format(", ".join(
    map(shorten, args.dimension)
)))

data = [
    (
        [
            SemType({
                CCD.CoreConceptQ: [CCD.CoreConceptQ],
                CCD.LayerA: [CCD.LayerA],
                CCD.NominalA: [CCD.RatioA]
            })
        ],
        [
            SemType({
                CCD.CoreConceptQ: [CCD.CoreConceptQ],
                CCD.LayerA: [CCD.LayerA],
                CCD.NominalA: [CCD.PlainRatioA]
            })
        ]
    )
]

solutions = wfsyn(
    io=data,
    solutions=args.solutions,
    types=Ontology.from_rdf(args.types),
    tools=Ontology.from_rdf(args.tools),
    dimensions=args.dimension,
)

for g in solutions:
    for s in g:
        print("Solution:")
        print(s.to_rdf().serialize(format="turtle").decode("utf-8"))
