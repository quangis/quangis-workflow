# -*- coding: utf-8 -*-
"""
Python wrapper for APE.

Takes an RDF based specification of tools with typed inputs and outputs and
turns it into an tool description in JSON according to the APE format

@author: Schei008
@date: 2019-03-22
@copyright: (c) Schei008 2019
@license: MIT
"""

import rdf_namespaces
from rdf_namespaces import TOOLS, WF, CCD, shorten
import semantic_dimensions
import errors

from rdflib.namespace import RDF
from rdflib import URIRef
import os
import logging
import subprocess
import tempfile
import json
from six.moves.urllib.parse import urldefrag


def downcast(node: URIRef) -> URIRef:
    """
    Downcast certain nodes to identifiable leafnodes. APE has a closed world
    assumption, in that it considers the set of leaf nodes it knows about as
    exhaustive: it will never consider parent nodes as valid answers.
    """
    if node == CCD.NominalA:
        return CCD.PlainNominalA
    elif node == CCD.OrdinalA:
        return CCD.PlainOrdinalA
    elif node == CCD.IntervalA:
        return CCD.PlainIntervalA
    elif node == CCD.RatioA:
        return CCD.PlainRatioA
    else:
        return node


def frag(node):
    return urldefrag(node).fragment


class WorkflowType:
    """
    Ontological classes of input or output types across different semantic
    dimensions.
    """

    def __init__(self, types):
        """
        @param types: A dictionary mapping dimensions to one or more classes.
        """

        self._type = {
            dimension:
                ontology_class
                if type(ontology_class) == list else
                [ontology_class]
            for dimension, ontology_class in types.items()
        }

    def __str__(self):
        return \
            ",".join(
                "&".join(
                    shorten(c) for c in cs
                )
                for d, cs in self._type.items()
            )

    def as_ape(self):
        return self._type

    def check_dimensions(self, dimensions=semantic_dimensions.CORE):
        """
        Check if all dimensions of our classes correspond to the ones under
        consideration.
        """
        for dimension in self._type.keys():
            if dimension not in dimensions:
                raise errors.WrongDimensionError(dimension, dimensions)


class WorkflowIO:
    """
    Sets of inputs or output types. For APE.
    """

    def __init__(self, dimensions=semantic_dimensions.CORE, *elements):
        self.dimensions = dimensions
        self.elements = elements

        for e in elements:
            e.check_dimensions(dimensions)

    def as_ape(self):
        """
        List of dictionaries, as expected by APE.
        """
        return [e.as_ape() for e in self.elements]

    def __str__(self):
        return \
            " ; ".join(str(e) for e in self.elements)


def configuration(
        ontology_path,
        tool_annotations_path,
        dimensions,
        inputs,
        outputs,
        prefix=CCD,
        tools_taxonomy_root=TOOLS.Tool,
        solution_length=(1, 10),
        max_solutions=5):
    """
    Prepare a dictionary containing APE configuration.
    """

    return {
        "solutions_dir_path": None,  # Will be overwritten
        "constraints_path": None,  # Will be overwritten
        "ontology_path": ontology_path,
        "tool_annotations_path": tool_annotations_path,
        "ontologyPrexifIRI": str(prefix),
        "toolsTaxonomyRoot": str(tools_taxonomy_root),
        "dataDimensionsTaxonomyRoots": [frag(iri) for iri in dimensions],
        "solution_length": {"min": solution_length[0],
                            "max": solution_length[1]},
        "max_solutions": max_solutions,
        "inputs": inputs.as_ape(),
        "outputs": outputs.as_ape(),
        "number_of_execution_scripts": 0,
        "number_of_generated_graphs": 0,
        "debug_mode": False,
        "shared_memory": True,
        "tool_seq_repeat": False,
        "use_workflow_input": "ALL",
        "use_all_generated_data": "ALL",
    }


def parse_solution(line):
    """
    Parse the file with APE's solutions.
    """
    return line.split(" ")


def run(executable, configuration):
    """
    Run APE.

    @param executable: Path to APE jar-file.
    @param configuration: Dictionary representing APE configuration object.
    """

    tmp = tempfile.mkdtemp(prefix="ape-")
    configuration['solutions_dir_path'] = tmp

    constraints_path = os.path.join(tmp, "constraints.json")
    configuration['constraints_path'] = constraints_path
    with open(constraints_path, 'w') as f:
        json.dump({"constraints": []}, f)

    config_path = os.path.join(tmp, "config.json")
    with open(config_path, 'w') as f:
        json.dump(configuration, f)

    try:
        logging.debug("Running APE in {}...".format(tmp))
        subprocess.run(["java", "-jar", executable, config_path], check=True)

        solutions_path = os.path.join(tmp, "solutions.txt")
        if os.path.exists(solutions_path):
            with open(solutions_path, 'r') as f:
                solutions = [parse_solution(line) for line in f.readlines()]
        else:
            solutions = []

        os.remove(solutions_path)
    finally:
        os.remove(constraints_path)
        os.remove(config_path)
        os.rmdir(tmp)

    return solutions
