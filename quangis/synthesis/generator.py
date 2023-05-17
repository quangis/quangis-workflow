#!/usr/bin/env python3
"""Higher-level APE wrapper that takes input and produces output in the RDF 
form we want it to."""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph
from rdflib.util import guess_format
from typing import Iterable
from transforge.namespace import shorten

from quangis.ccd import ccd_graph, dimensions
from quangis.polytype import Polytype
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA, WF
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
            tool_root=TOOLS.Tool,
            namespace=CCD,
            build_dir=build_dir,
            dimensions=[d.root for d in self.dimensions]
        )

    def ape_tools(self) -> ToolsDict:
        """
        Convert tool annotation graph into a dictionary that APE understands.
        """

        input_predicates = (WF.input1, WF.input2, WF.input3)
        output_predicates = (WF.output, WF.output2, WF.output3)

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
                        for p in input_predicates
                        if (input := self.tools.value(tool, p, any=False))
                    ],
                    'outputs': [
                        {
                            k.root: list(v)
                            for k, v in Polytype.project(
                                self.dimensions,
                                self.tools.objects(output, RDF.type)
                            ).downcast(casts).items()
                        }
                        for p in output_predicates
                        if (output := self.tools.value(tool, p, any=False))
                    ]
                }
                for tool in self.tools.objects(predicate=TOOLS.implements)
            ]
        }

    def ape_tool_taxonomy(self) -> Graph:
        taxonomy = Graph()
        taxonomy.base = CCD

        for s, o in self.tools.subject_objects(TOOLS.implements):
            taxonomy.add((o, RDFS.subClassOf, s))
            taxonomy.add((s, RDF.type, OWL.Class))
            taxonomy.add((o, RDF.type, OWL.Class))
            taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))
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
