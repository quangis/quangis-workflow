"""
Higher-level APE wrapper that takes input and produces output in the RDF form
we want it to.
"""

import itertools
from rdflib import URIRef, BNode
from typing import List

from quangis.semtype import SemType
from quangis.namespace import CCD, TOOLS, OWL, RDF, RDFS, ADA, WF
from quangis.ontology import Ontology
from quangis.taxonomy import Taxonomy
from quangis.util import shorten
from quangis.wfsyn import ape


def get_resources(
        tools: Ontology,
        tool: URIRef,
        is_output: bool) -> List[BNode]:
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


def get_types(tools: Ontology, resource: BNode) -> List[URIRef]:
    """
    Returns a list of types of some tool input/output resource.
    """
    return list(tools.objects(resource, RDF.type))


def ape_tools(
        tools: Ontology, dimensions: List[Taxonomy]) -> ape.ToolsDict:
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
                    SemType.project(
                        dimensions, get_types(tools, resource)
                    ).to_dict()
                    for resource in get_resources(tools, tool, is_output=False)
                ],
                'outputs': [
                    SemType.project(
                        dimensions, get_types(tools, resource)
                    ).downcast().to_dict()
                    for resource in get_resources(tools, tool, is_output=True)
                ]
            }
            for tool in tools.objects(predicate=TOOLS.implements)
        ]
    }


def ape_taxonomy(
        types: Ontology,
        tools: Ontology,
        dimensions: List[Taxonomy]) -> Ontology:
    """
    Extracts a taxonomy of toolnames from the tool description combined with a
    core OWL taxonomy of types.
    """

    taxonomy = Ontology()

    for (s, p, o) in tools.triples((None, TOOLS.implements, None)):
        taxonomy.add((o, RDFS.subClassOf, s))
        taxonomy.add((s, RDF.type, OWL.Class))
        taxonomy.add((o, RDF.type, OWL.Class))
        taxonomy.add((s, RDFS.subClassOf, TOOLS.Tool))

    # Only keep subclass nodes intersecting with exactly one dimension
    for (o, p, s) in itertools.chain(
            types.triples((None, RDFS.subClassOf, None)),
            types.triples((None, RDF.type, OWL.Class))
            ):
        if type(s) != BNode and type(o) != BNode \
                and s != o and s != OWL.Nothing and \
                types.dimensionality(o, [d.root for d in dimensions]) == 1:
            taxonomy.add((o, p, s))

    # Add common upper class for all data types
    taxonomy.add((CCD.Attribute, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.SpatialDataSet, RDFS.subClassOf, CCD.DType))
    taxonomy.add((ADA.Quality, RDFS.subClassOf, CCD.DType))

    return taxonomy


class WorkflowSynthesis(ape.APE):
    """
    A wrapper around the lower-level APE wrapper that takes input and output in
    the form we want it to.
    """

    def __init__(
            self,
            types: Ontology,
            tools: Ontology,
            dimensions: List[Taxonomy]):
        super().__init__(
            taxonomy=ape_taxonomy(types, tools, dimensions),
            tools=ape_tools(tools, dimensions),
            tool_root=TOOLS.Tool,
            namespace=CCD,
            dimensions=[d.root for d in dimensions]
        )

    def run(self, *nargs, **kwargs) -> List[ape.Workflow]:
        return super().run(*nargs, **kwargs)
