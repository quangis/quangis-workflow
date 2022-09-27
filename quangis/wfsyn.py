#!/usr/bin/env python3
"""
Higher-level APE wrapper that takes input and produces output in the RDF form
we want it to.

When run: A workflow generator: command-line interface to APE that generates
input data from a given OWL data ontology and a given tool annotation file, by
projecting classes to ontology dimensions.
"""

import os.path
import argparse
import logging
import urllib.request
from itertools import chain, product
from importlib import reload
from rdflib import Graph
from rdflib.term import Node, BNode
from apey import APE, Workflow, ToolsDict
from cct import cct
from transformation_algebra.util.common import build_transformation

from quangis.semtype import SemType, Dimension
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA, WF
from quangis.util import uri, shorten


def get_resources(
        tools: Graph,
        tool: Node,
        is_output: bool) -> list[Node]:
    """
    Get the input/output resource nodes associated with a tool.
    """
    if is_output:
        predicates = (WF.output, WF.output2, WF.output3)
    else:
        predicates = (WF.input1, WF.input2, WF.input3)

    resources = []
    for p in predicates:
        resource = tools.value(predicate=p, subject=tool, any=False)
        if resource:
            resources.append(resource)
    return resources


def get_types(tools: Graph, resource: Node) -> list[Node]:
    """
    Returns a list of types of some tool input/output resource.
    """
    return list(tools.objects(resource, RDF.type))


def ape_tools(tools: Graph, dimensions: list[Dimension]) -> ToolsDict:
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    return {
        'functions': [
            {
                'id': str(tool),
                'label': shorten(tool),
                'taxonomyOperations': [tool],
                'inputs': [
                    {
                        k: list(v)
                        for k, v in
                        SemType.project(
                            dimensions, get_types(tools, resource)
                        ).items()
                    }
                    for resource in get_resources(tools, tool, is_output=False)
                ],
                'outputs': [
                    {
                        k: list(v)
                        for k, v in
                        SemType.project(
                            dimensions, get_types(tools, resource)
                        ).downcast().items()
                    }
                    for resource in get_resources(tools, tool, is_output=True)
                ]
            }
            for tool in tools.objects(predicate=TOOLS.implements)
        ]
    }


def ape_taxonomy(
        types: Graph, tools: Graph, dimensions: list[Dimension]) -> Graph:
    """
    Extracts a taxonomy of toolnames from the tool description combined with a
    core OWL taxonomy of types.
    """

    taxonomy = Graph()

    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        taxonomy.add((o, RDFS.subClassOf, s))
        taxonomy.add((s, RDF.type, OWL.Class))
        taxonomy.add((o, RDF.type, OWL.Class))
        taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))

    # Only keep subclass nodes that intersect with exactly one dimension
    for o, p, s in chain(
            types.triples((None, RDFS.subClassOf, None)),
            types.triples((None, RDF.type, OWL.Class))):
        if (isinstance(s, BNode) or isinstance(o, BNode)
                or s == o or s == OWL.Nothing):
            continue

        if sum(1 for dim in dimensions if o in dim) == 1:
            taxonomy.add((o, p, s))

    # Add common upper class for all data types
    taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

    return taxonomy


class WorkflowSynthesis(APE):
    """
    A wrapper around the lower-level APE wrapper that takes input and output in
    the form we want it to.
    """

    def __init__(self, types: Graph, tools: Graph, dimensions: list[Dimension]):
        super().__init__(
            taxonomy=ape_taxonomy(types, tools, dimensions),
            tools=ape_tools(tools, dimensions),
            tool_root=TOOLS.Tool,
            namespace=CCD,
            dimensions=[d.root for d in dimensions]
        )

    def run(self, *nargs, **kwargs) -> list[Workflow]:
        return super().run(*nargs, **kwargs)


def get_data(fn: str, dimensions: list[Dimension]) -> list[SemType]:
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


if __name__ == '__main__':
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
        default=1,
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
            url="https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl"
        )

    logging.info("Dimensions: {}".format(", ".join(
        map(shorten, args.dimension)
    )))

    logging.info("Reading RDF...")
    types = Graph()
    types.parse(args.types, format='xml')
    tools = Graph()
    tools.parse(args.tools, format='ttl')

    logging.info("Compute subsumption trees for the dimensions...")
    dimensions = [Dimension(d, types) for d in args.dimension]

    logging.info("Starting APE...")
    wfsyn = WorkflowSynthesis(types=types, tools=tools, dimensions=dimensions)

    logging.info("Reading input data {}...".format(args.inputs))
    inputs = get_data(args.inputs, dimensions)

    logging.info("Reading output data {}...".format(args.outputs))
    outputs = get_data(args.outputs, dimensions)

    running_total = 0
    for i, o in product(inputs, outputs):
        logging.info("Running synthesis for {} -> {}".format(i, o))
        solutions = wfsyn.run(
            inputs=[i],
            outputs=[o],
            solutions=args.solutions)
        for s in solutions:
            fn = f"solution{shorten(s.root)}.ttl"
            print("Building transformation graph...")
            g = build_transformation(cct, tools, s)
            print(f"Writing solution {fn}")
            g.serialize(fn, format="ttl")

        running_total += len(solutions)
        logging.info("Running total: {}".format(running_total))
