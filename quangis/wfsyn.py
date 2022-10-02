#!/usr/bin/env python3
"""
Higher-level APE wrapper that takes input and produces output in the RDF form
we want it to.

When run: A workflow generator: command-line interface to APE that generates
input data from a given OWL data ontology and a given tool annotation file, by
projecting classes to ontology dimensions.
"""

import urllib.request
from pathlib import Path
from itertools import product
from rdflib import Graph
from rdflib.term import Node
from cct import cct
from transformation_algebra.util.common import build_transformation
from typing import Iterable

from quangis.ape import APE, Workflow, ToolsDict
from quangis.dimtypes import DimTypes, Dimension
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA, WF
from quangis.util import uri, shorten


class CCDWorkflowSynthesis(APE):
    """
    A wrapper around the lower-level APE wrapper that takes input and output in
    the form we want it to.
    """

    def __init__(self, ccd_types: Graph, tools: Graph, dimensions: list[Node]):

        self.tools = tools
        self.ccd_types = ccd_types
        self.dimensions = [Dimension(d, ccd_types) for d in dimensions]

        super().__init__(
            taxonomy=self.ape_taxonomy(),
            tools=self.ape_tools(),
            tool_root=TOOLS.Tool,
            namespace=CCD,
            dimensions=[d.root for d in self.dimensions]
        )

    def ape_tools(self) -> ToolsDict:
        """
        Convert tool annotation graph into a dictionary that APE understands.
        """

        input_predicates = (WF.input1, WF.input2, WF.input3)
        output_predicates = (WF.output, WF.output2, WF.output3)

        return {
            'functions': [
                {
                    'id': str(tool),
                    'label': shorten(tool),
                    'taxonomyOperations': [tool],
                    'inputs': [
                        {
                            k.root: list(v) for k, v in
                            DimTypes.project(
                                self.dimensions,
                                tools.objects(resource, RDF.type)
                            ).items()
                        }
                        for p in input_predicates
                        if (resource := self.tools.value(tool, p, any=False))
                    ],
                    'outputs': [
                        {
                            k.root: list(v) for k, v in
                            DimTypes.project(
                                self.dimensions,
                                tools.objects(resource, RDF.type)
                            ).downcast().items()
                        }
                        for p in output_predicates
                        if (resource := self.tools.value(tool, p, any=False))
                    ]
                }
                for tool in tools.objects(predicate=TOOLS.implements)
            ]
        }

    def ape_taxonomy(self) -> Graph:
        """
        Extracts a taxonomy of GIS tools and CCD types.
        """

        taxonomy = Graph()

        for s, o in self.tools.subject_objects(TOOLS.implements):
            taxonomy.add((o, RDFS.subClassOf, s))
            taxonomy.add((s, RDF.type, OWL.Class))
            taxonomy.add((o, RDF.type, OWL.Class))
            taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))

        for s, o in self.ccd_types.subject_objects(RDFS.subClassOf):
            # Only keep nodes that intersect with exactly one dimension
            if sum(1 for dim in self.dimensions if dim.contains(s)) == 1:
                taxonomy.add((s, RDFS.subClassOf, o))
                taxonomy.add((s, RDF.type, OWL.Class))
                taxonomy.add((o, RDF.type, OWL.Class))

        # Add common upper class for all data types
        taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
        taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
        taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

        return taxonomy

    def run(self, *nargs, **kwargs) -> Iterable[Workflow]:
        return super().run(*nargs, **kwargs)


def get_data(fn: Path, dimensions: list[Dimension]) -> list[DimTypes]:
    """
    Read a newline-separated file of `DimTypes` represented by comma-separated
    URIs.
    """
    result = []
    with open(fn, 'r') as f:
        for line in f.readlines():
            types = (x.strip() for x in line.split("#")[0].split(","))
            result.append(
                DimTypes.project(dimensions, [uri(t) for t in types if t])
            )
    return result


def download_if_missing(path: Path, url: str) -> Path:
    """
    Make sure that a file exists by downloading it if it doesn't exist. Return
    filename.
    """

    directory = path.parent
    directory.mkdir(exist_ok=True)
    if not path.exists():
        print(f"{path} not found; now downloading from {url}")
        urllib.request.urlretrieve(url, filename=path)

    return path


if __name__ == '__main__':

    data_dir = Path(__file__).parent.parent / "data"

    tools_file = download_if_missing(
        path=data_dir / "ToolDescription.ttl",
        url="https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl"
    )

    types_file = download_if_missing(
        path=data_dir / "CoreConceptData.rdf",
        url="http://geographicknowledge.de/vocab/CoreConceptData.rdf"
    )

    types = Graph()
    types.parse(types_file, format='xml')
    tools = Graph()
    tools.parse(tools_file, format='ttl')

    dimensions = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]

    wfsyn = CCDWorkflowSynthesis(ccd_types=types, tools=tools,
        dimensions=dimensions)

    inputs = get_data(data_dir / "sources.txt", wfsyn.dimensions)
    outputs = get_data(data_dir / "goals.txt", wfsyn.dimensions)

    running_total = 0
    for i, o in product(inputs, outputs):
        print("Running synthesis for {} -> {}".format(i, o))
        solutions = wfsyn.run(
            inputs=[i],
            outputs=[o],
            solutions=1)
        for solution in solutions:
            running_total += 1
            print("Building transformation graph...")
            g = build_transformation(cct, tools, solution)
            print(g.serialize(format="ttl"))
            g.serialize(f"solution{shorten(solution.root)}.ttl", format="ttl")
        print("Running total: {}".format(running_total))
