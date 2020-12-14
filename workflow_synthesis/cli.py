#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A workflow generator: a wrapper for APE that generates input data from a given
OWL data ontology and a given tool annotation file, by projecting classes to
ontology dimensions.

When run on its own, this is a command-line interface to the APE wrapper.

@author: Schei008
@date: 2020-04-08
@copyright: (c) Schei008 2020
@license: MIT
"""

import taxonomy
import semantic_dimensions
import ape
import rdf_namespaces
from utils import load_rdf, download_if_missing

import os.path
import argparse
import json
import logging


def wfsyn(types,
          tools,
          dimensions=semantic_dimensions.CORE):

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    types_tax = taxonomy.clean_owl_ontology(types, dimensions)
    tools_tax = taxonomy.extract_tool_ontology(tools)

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file, and clear the ontology
    # from non-core nodes
    _, projection = \
        semantic_dimensions.project(taxonomy=types_tax, dimnodes=dimensions)

    # Combine tool & type taxonomies
    taxonomies = tools_tax + types_tax

    # Transform tool annotations with the projected classes into APE input
    tools_ape = ape.tool_annotations(tools, projection, dimensions)

    return taxonomies, tools_ape


def ns(n):
    """
    Quick way to convert strings to namespaces
    """
    n = n.strip()
    if n == "ccd":
        return rdf_namespaces.CCD
    elif n == "em" or n == "exm":
        return rdf_namespaces.EXM
    else:
        print(n)


def test(path, dimensions):
    """
    Quick testing function with the provided data.
    """
    sets = []
    cur = []
    with open(path) as f:
        for line in f.readlines():
            cs = line.split(",")
            if len(cs) >= 3:
                cur.append({
                    dimensions[i]: ns(cs[i].split(":")[0])[cs[i].split(":")[1].strip()]
                    for i in range(0, 3)
                })
            else:
                sets.append(cur)
                cur = []
    if cur:
        sets.append(cur)
    return sets


if __name__ == '__main__':

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    parser = argparse.ArgumentParser(
        description="Wrapper for APE that synthesises CCD workflows"
    )

    parser.add_argument(
        '--ape',
        help="path to APE .jar executable")

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
        '--logging',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help="Level of information logged to the terminal")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.logging.upper()))

    if not args.ape:
        args.ape = download_if_missing(
            path=os.path.join(args.output, "APE-1.0.2-executable.jar"),
            url="https://github.com/sanctuuary/APE/releases/download/v1.0.2/"
                "APE-1.0.2-executable.jar")

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

    dimensions = semantic_dimensions.CORE

    # Prepare data files needed by APE
    taxonomy_file = os.path.join(args.output, "GISTaxonomy.rdf")
    tools_file = os.path.join(args.output, "ToolDescription.json")

    tax, tools = wfsyn(
        types=load_rdf(args.types),
        tools=load_rdf(args.tools),
        dimensions=dimensions)

    tax.serialize(destination=taxonomy_file, format='xml')
    with open(tools_file, 'w') as f:
        json.dump(tools, f, sort_keys=True, indent=2)

    # Quick
    input_sets = test("data/sources.txt", dimensions)
    output_sets = test("data/goals.txt", dimensions)

    # Run APE
    for inputs in input_sets:
        for outputs in output_sets:
            solutions = ape.run(
                executable=args.ape,
                configuration=ape.configuration(
                    ontology_path=taxonomy_file,
                    tool_annotations_path=tools_file,
                    dimensions=dimensions,
                    inputs=inputs,
                    outputs=outputs
                )
            )
            for solution in solutions:
                logging.critical(solution)

