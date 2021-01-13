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
import tool_description
from ontology import Ontology
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
        help="tool annotations in RDF")

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
    # dimensions = [CCD.DType]
    # dimensions = [CCD.CoreConceptQ, CCD.LayerA]

    # Prepare data files needed by APE
    taxonomy_file = os.path.join(args.output, "GISTaxonomy.rdf")
    tools_file = os.path.join(args.output, "ToolDescription.json")

    logging.critical("Loading ontologies...")
    types = Ontology.from_rdf(args.types)
    tools = Ontology.from_rdf(args.tools)

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    logging.critical("Compute taxonomies...")
    types_tax = ontology.clean_owl_ontology(types, dimensions)
    tools_tax = ontology.extract_tool_ontology(tools)

    types_tax.debug()

    tools_tax.debug()

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file, and clear the ontology
    # from non-core nodes --> not actually done!
    logging.critical("Compute projected classes...")
    projection = \
        semtype.project(taxonomy=types_tax, dimensions=dimensions)

    # Combine tool & type taxonomies
    logging.critical("Combine taxonomies...")
    taxonomies = tools_tax + types_tax.core(dimensions)

    # Transform tool annotations with the projected classes into APE input
    logging.critical("Transform tool annotations...")
    tools_ape = tool_description.ontology_to_json(tools, projection, dimensions)

    # Serialize both
    taxonomies.serialize(destination=taxonomy_file, format='xml')
    with open(tools_file, 'w') as f:
        json.dump(tools_ape, f, sort_keys=True, indent=2)

    # Quick
    # input_sets = test("data/sources.txt", dimensions)
    # output_sets = test("data/goals.txt", dimensions)

    logging.debug("Running APE...")

    # Run APE
    jvm = ape.APE(
        taxonomy=taxonomy_file,
        tools=tools_file,
        tool_root=TOOLS.Tool,
        namespace=CCD,
        dimensions=dimensions)

    # for inputs in input_sets:
    #    for outputs in output_sets:

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
