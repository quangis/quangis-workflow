#!/usr/bin/env python3
"""
A workflow generator: command-line interface to APE that generates input data
from a given OWL data ontology and a given tool annotation file, by projecting
classes to ontology dimensions.
"""

import os.path
import argparse
import logging
import itertools
import urllib.request
from importlib import reload
from typing import List

from quangis.namespace import CCD
from quangis.semtype import SemType
from quangis.ontology import Ontology
from quangis.taxonomy import Taxonomy
from quangis.wfsyn import WorkflowSynthesis
from quangis.util import uri, shorten


def get_data(fn: str, dimensions: List[Taxonomy]) -> List[SemType]:
    """
    Read a newline-separated file of SemTypes represented by comma-separated
    URIs.
    """
    result = []
    with open(fn, 'r') as f:
        for line in f.readlines():
            types = (x.strip() for x in line.split("#")[0].split(","))
            result.append(
                SemType.project(dimensions, [uri(t) for t in types if t])
            )
    return result


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
    '--inputs',
    default=os.path.join('data', 'sources.txt'),
    help="file containing input types")

parser.add_argument(
    '--outputs',
    default=os.path.join('data', 'goals.txt'),
    help="file containing output types")

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

logging.info("Reading RDF...")
types = Ontology.from_rdf(args.types)
tools = Ontology.from_rdf(args.tools)

logging.info("Compute subsumption trees for the dimensions...")
dimensions = [Taxonomy.from_ontology(types, d) for d in args.dimension]

logging.info("Starting APE...")
wfsyn = WorkflowSynthesis(types=types, tools=tools, dimensions=dimensions)

logging.info("Reading input data {}...".format(args.inputs))
inputs = get_data(args.inputs, dimensions)

logging.info("Reading output data {}...".format(args.outputs))
outputs = get_data(args.outputs, dimensions)

running_total = 0
for i, o in itertools.product(inputs, outputs):
    logging.info("Running synthesis for {} -> {}".format(i, o))
    solutions = wfsyn.run(
        inputs=[i],
        outputs=[o],
        solutions=args.solutions)
    for s in solutions:
        print("Solution:")
        print(s.to_rdf().serialize(format="turtle").decode("utf-8"))

    running_total += len(solutions)
    logging.info("Running total: {}".format(running_total))
