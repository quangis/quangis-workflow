#!/usr/bin/env python3
"""
A workflow generator: a wrapper for APE that generates input data from a given
OWL data ontology and a given tool annotation file, by projecting classes to
ontology dimensions.

When run on its own, this is a command-line interface to the APE wrapper.
"""

import os.path
import argparse
import json
import logging

import ape
import ontology
import semtype
from wfsyn import wfsyn
from ontology import Ontology
from ontology.tool import ontology_to_json
from namespace import CCD, TOOLS
from semtype import SemType
from utils import download_if_missing

if __name__ == '__main__':

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    parser = argparse.ArgumentParser(
        description="Wrapper for APE that synthesises CCD workflows"
    )

    parser.add_argument(
        '-o', '--output',
        default=os.path.join(ROOT_DIR, "build"),
        help="output directory")

    parser.add_argument(
        '--types',
        help="core concept datatype ontology in RDF")

    parser.add_argument(
        '--tools',
        help="tool annotation ontology in RDF")

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
    from importlib import reload
    reload(logging)
    logging.basicConfig(
        level=getattr(logging, args.log.upper()),
        format="\033[1m%(asctime)s \033[0m%(message)s",
    )

    if not args.types:
        # args.types = download_if_missing(
        #    path=os.path.join(args.output, "CoreConceptData.rdf"),
        #    url="http://geographicknowledge.de/vocab/CoreConceptData.rdf"
        # )
        args.types = download_if_missing(
            path=os.path.join(args.output, "CoreConceptData.ttl"),
            url="https://raw.githubusercontent.com/simonscheider/QuAnGIS/"
                "master/Ontology/CoreConceptData.ttl"
        )

    if not args.tools:
        # args.tools = download_if_missing(
        #    path=os.path.join(args.output, "GISTools.rdf"),
        #    url="http://geographicknowledge.de/vocab/GISTools.rdf"
        # )
        args.tools = download_if_missing(
            path=os.path.join(args.output, "ToolDescription.ttl"),
            url="https://raw.githubusercontent.com/simonscheider/QuAnGIS/"
                "master/ToolRepository/ToolDescription.ttl"
        )

    dimensions = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
    types = Ontology.from_rdf(args.types)
    tools = Ontology.from_rdf(args.tools)

    tax, tools_ape = wfsyn(types, tools, dimensions)

    logging.debug("Running APE...")
    jvm = ape.APE(
        taxonomy=tax,
        tools=tools_ape,
        tool_root=TOOLS.Tool,
        namespace=CCD,
        dimensions=dimensions)

    inputs = [
        SemType({
            CCD.CoreConceptQ: [CCD.CoreConceptQ],
            CCD.LayerA: [CCD.LayerA],
            CCD.NominalA: [CCD.RatioA]
        })
    ]
    outputs = [
        SemType({
            CCD.CoreConceptQ: [CCD.CoreConceptQ],
            CCD.LayerA: [CCD.LayerA],
            CCD.NominalA: [CCD.PlainRatioA]
        })
    ]

    logging.info("Finding workflows for {} -> {}".format(str(inputs[0]), str(outputs[0])))
    solutions = jvm.run(
        inputs=inputs,
        outputs=outputs,
        solutions=args.solutions)

    for s in solutions:
        print("Solution:")
        print(s.to_rdf().serialize(format="turtle").decode("utf-8"))
