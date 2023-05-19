"""Higher-level APE wrapper that takes input in the desired form."""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph
from rdflib.util import guess_format
from typing import Iterable
from transforge.namespace import shorten

from quangis.ccdata import ccd_graph, dimensions
from quangis.polytype import Polytype
from quangis.namespace import CCD, VOCAB, OWL, RDF, RDFS, ADA
from quangis.synthesis.ape import APE, Workflow, ToolsDict

def graph(path: Path) -> Graph:
    g = Graph()
    g.parse(path, format=guess_format(str(path)))
    return g


class WorkflowGenerator(APE):
    """
    A wrapper around the lower-level APE wrapper that takes input and output in
    the form we want it to.
    """

    def __init__(self, tools: Path, build_dir: Path):
        self.types = ccd_graph
        self.tools = graph(tools)
        self.dimensions = dimensions

        super().__init__(
            taxonomy=self.ape_type_taxonomy() + self.ape_tool_taxonomy(),
            tools=self.ape_tools(),
            tool_root=VOCAB.Abstraction,
            namespace=CCD,
            build_dir=build_dir,
            dimensions=[d.root for d in self.dimensions]
        )

    def ape_tools(self) -> ToolsDict:
        """
        Convert tool annotation graph into a dictionary that APE understands.
        """

        casts = {
            CCD.NominalA: CCD.PlainNominalA,
            CCD.OrdinalA: CCD.PlainOrdinalA,
            CCD.IntervalA: CCD.PlainIntervalA,
            CCD.RatioA: CCD.PlainRatioA}

        return {
            'functions': [
                {
                    'id': str(tool),
                    'label': shorten(tool),
                    'taxonomyOperations': [tool],
                    'inputs': [
                        {
                            k.root: list(v)
                            for k, v in Polytype.project(
                                self.dimensions,
                                self.tools.objects(input, RDF.type)
                            ).items()
                        }
                        for input in self.tools.objects(tool, VOCAB.output)
                    ],
                    'outputs': [
                        {
                            k.root: list(v)
                            for k, v in Polytype.project(
                                self.dimensions,
                                self.tools.objects(output, RDF.type)
                            ).downcast(casts).items()
                        }
                        for output in self.tools.objects(tool, VOCAB.output)
                    ]
                }
                for tool in self.tools.subjects(RDF.type, VOCAB.Abstraction)
            ]
        }

    def ape_tool_taxonomy(self) -> Graph:
        taxonomy = Graph()
        taxonomy.base = CCD

        for tool in self.tools.subjects(RDF.type, VOCAB.Abstraction):
            taxonomy.add((tool, RDF.type, OWL.Class))
            taxonomy.add((tool, RDFS.subClassOf, VOCAB.Abstraction))
        return taxonomy

    def ape_type_taxonomy(self) -> Graph:
        """
        Extracts a taxonomy of CCD types.
        """

        taxonomy = Graph()
        taxonomy.base = CCD

        for s, o in self.types.subject_objects(RDFS.subClassOf):
            # Only keep nodes that intersect with exactly one dimension
            if sum(1 for dim in self.dimensions if s in dim) == 1:
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
