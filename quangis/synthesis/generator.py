"""Higher-level APE wrapper that takes input in the desired form."""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph
from rdflib.util import guess_format
from itertools import chain
from transforge.namespace import shorten

from quangis.ccd import ccd
from quangis.polytype import Polytype
from quangis.namespace import CCD, TOOL, OWL, RDF, RDFS, ADA
from quangis.synthesis.ape import APE, ToolsDict

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
        self.tools = graph(tools)
        typetax = self.ape_type_taxonomy()
        tooltax = self.ape_tool_taxonomy()

        # Purely for troubleshooting
        for d in ccd.dimensions:
            d.graph.serialize(build_dir / f"dimension_{shorten(d.root)}.ttl")
        typetax.serialize(build_dir / "taxonomy_types.ttl")
        tooltax.serialize(build_dir / "taxonomy_tools.ttl")

        super().__init__(
            taxonomy=typetax + tooltax,
            tools=self.ape_tools(),
            tool_root=TOOL.Abstraction,
            ontology_prefix_iri=CCD,
            build_dir=build_dir,
            dimensions=[d.root for d in ccd.dimensions]
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
                                ccd.dimensions,
                                self.tools.objects(input, RDF.type)
                            ).items()
                        }
                        for input in self.tools.objects(tool, TOOL.input)
                    ],
                    'outputs': [
                        {
                            k.root: list(v)
                            for k, v in Polytype.project(
                                ccd.dimensions,
                                self.tools.objects(output, RDF.type)
                            ).downcast(casts).items()
                        }
                        for output in self.tools.objects(tool, TOOL.output)
                    ]
                }
                # for tool in self.tools.subjects(RDF.type, TOOL.Abstraction)
                for tool in self.tools.subjects(TOOL.implementation, None)
            ]
        }

    def ape_tool_taxonomy(self) -> Graph:
        """Extracts a taxonomy of tools and CCD types."""

        taxonomy = Graph()

        # This doesn't fully make sense --- why would a specific tool be a 
        # subclass of the class of tools? Why would a tool abstraction subclass 
        # a tool implementation? But this is the format in which it worked 
        # before, so...
        taxonomy.add((TOOL.Tool, RDFS.subClassOf, OWL.Class))
        for tool in chain(self.tools.subjects(RDF.type, TOOL.Unit), 
                self.tools.subjects(RDF.type, TOOL.Multi)):
            taxonomy.add((tool, RDF.type, OWL.Class))
            taxonomy.add((tool, RDFS.subClassOf, TOOL.Abstraction))

        for abstr, impl in self.tools.subject_objects(TOOL.implementation):
            taxonomy.add((abstr, RDF.type, OWL.Class))
            taxonomy.add((abstr, RDFS.subClassOf, impl))

        return taxonomy

    def ape_type_taxonomy(self) -> Graph:
        taxonomy = Graph()
        for s, o in ccd.subject_objects(RDFS.subClassOf):
            # Only keep nodes that intersect with exactly one dimension
            taxonomy.add((o, RDF.type, OWL.Class))
            if sum(1 for dim in ccd.dimensions if s in dim) == 1:
                taxonomy.add((s, RDFS.subClassOf, o))
                taxonomy.add((s, RDF.type, OWL.Class))

        # Add common upper class for all data types
        taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
        taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
        taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

        return taxonomy
