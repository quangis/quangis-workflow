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
import tool_annotations
from utils import load_rdf, download_if_missing

import os.path
import subprocess
import argparse
import json
import logging


def ape_config(outdir, ontology_file, tools_file):
    """
    Prepare JSON for APE configuration.
    """

    return {
      "ontologyPrexifIRI": "http://geographicknowledge.de/vocab/"
                           "CoreConceptData.rdf#",
      "toolsTaxonomyRoot": "http://geographicknowledge.de/vocab/"
                           "GISTools.rdf#Tool",
      "solutions_dir_path": outdir,
      "ontology_path": ontology_file,
      "tool_annotations_path": tools_file,
      "dataDimensionsTaxonomyRoots": [
        "CoreConceptQ",
        "LayerA",
        "NominalA"
      ],
      "shared_memory": "true",
      "solution_length": {"min": 1, "max": 10},
      "max_solutions": "5",
      "number_of_execution_scripts": "0",
      "number_of_generated_graphs": "5",
      "inputs": [
        {
            "CoreConceptQ": ["ObjectQ"],
            "LayerA": ["VectorTessellationA"],
            "NominalA": ["PlainNominalA"]
        },
        {
            "CoreConceptQ": ["ObjectQ"],
            "LayerA": ["VectorTessellationA"],
            "NominalA": ["PlainNominalA"]
        },
        {
            "CoreConceptQ": ["ObjectQ"],
            "LayerA": ["PointA"],
            "NominalA": ["PlainNominalA"]
        }
      ],
      "outputs": [
        {
            "CoreConceptQ": ["ObjectQ"],
            "LayerA": ["VectorA", "TessellationA"],
            "NominalA": ["CountA"]
        }
      ],
      "debug_mode": "true",
      "use_workflow_input": "all",
      "use_all_generated_data": "all",
      "tool_seq_repeat": "false"
    }


def wfsyn(types,
          tools,
          dimensions=semantic_dimensions.CORE):

    # Generates a taxonomy version of the ontology as well as of the given tool
    # hierarchy (using rdfs:subClassOf), by applying reasoning and removing all
    # other statements
    types_tax = taxonomy.cleanOWLOntology(types)
    tools_tax = taxonomy.extractToolOntology(tools)

    # Computes a projection of classes to any of a given set of dimensions
    # given by superconcepts in the type taxonomy file, and clear the ontology
    # from non-core nodes
    types, projection = \
        semantic_dimensions.project(taxonomy=types_tax, dimnodes=dimensions)

    # Combine tool & type taxonomies
    taxonomies = tools_tax + types_tax

    # Transform tool annotations with the projected classes into APE input
    tools_ape = tool_annotations.rdf2ape(tools, projection, dimensions)

    return taxonomies, tools_ape


if __name__ == '__main__':

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    parser = argparse.ArgumentParser(
        description="Wrapper for APE that synthesises CCD workflows"
    )

    parser.add_argument('--ape',
                        help="path to APE .jar executable")

    parser.add_argument('-o', '--output',
                        default=os.path.join(ROOT_DIR, "build"),
                        help="output directory")

    parser.add_argument('--types',
                        help="core concept datatype ontology in RDF")

    parser.add_argument('--tools',
                        help="tool annotations in RDF")

    parser.add_argument('--logging',
                        choices=['debug', 'info', 'warning', 'error',
                                 'critical'],
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

    # Prepare data needed by APE
    tax, tools = wfsyn(types=load_rdf(args.types), tools=load_rdf(args.tools))

    # Prepare files needed by APE
    taxonomy_file = os.path.join(args.output, "GISTaxonomy.rdf")
    tax.serialize(destination=taxonomy_file, format='xml')

    tools_file = os.path.join(args.output, "ToolDescription.json")
    with open(tools_file, 'w') as f:
        json.dump(tools, f, sort_keys=True, indent=2)

    ape_config_file = os.path.join(args.output, "ape.json")
    with open(ape_config_file, 'w') as f:
        json.dump(ape_config(args.output, taxonomy_file, tools_file), f)

    # Run APE
    subprocess.call(["java", "-jar", args.ape, ape_config_file])

