"""
This module contains functions to work with tool annotations.
"""

from rdflib import Graph, URIRef, Namespace
from rdflib.term import Node
from rdflib.namespaces import RDF
from typing import Mapping, Iterable

import logging

from rdf_namespaces import TOOLS, WF, CCD, shorten


def getinoutypes(g,
                 predicate,
                 subject,
                 project,
                 dimix,
                 dim,
                 namespace):
    """
    Returns a list of types of some tool input/output which are all projected
    to given semantic dimension
    """

    inoutput = g.value(predicate=predicate, subject=subject, any=False)
    if not inoutput:
        raise Exception(
            f'Could not find object with subject {subject} and predicate {predicate}!'
        )

    outputtypes = []
    for outputtype in g.objects(inoutput, RDF.type):
        if outputtype is not None and outputtype in project:
            if project[outputtype][dimix] is not None:
                outputtypes.append(project[outputtype][dimix])

    return outputtypes or [dim]


#    if dodowncast:
        # Downcast is used to enforce leaf nodes for types. Is used to make
        # annotations as specific as possible, used only for output nodes
#        outputtypes = [downcast(t) for t in outputtypes]

    # In case there is no type, just use the highest level type of the
    # corresponding dimension
#    if out == []:
#        if dodowncast:
#            out = [shortURInames(downcast(dim))]
#        else:


def tool_annotations(
        trdf: Graph,
        project: Mapping[Node, Node],
        dimensions: Iterable[URIRef],
        namespace: Namespace = CCD):
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    logging.info("Converting RDF tool annotations to APE format...")

    toollist = []
    for t in trdf.objects(None, TOOLS.implements):
        inputs = []
        for p in [WF.input1, WF.input2, WF.input3]:

            if trdf.value(subject=t, predicate=p, default=None) is not None:
                d = {}
                for ix, dim in enumerate(dimensions):
                    d[dim] = getinoutypes(
                        trdf, p, t, project, ix, dim, namespace)
                inputs += [d]
        outputs = []

        for p in [WF.output, WF.output2, WF.output3]:
            if trdf.value(subject=t, predicate=p, default=None) is not None:
                d = {}
                for ix, dim in enumerate(dimensions):
                    d[dim] = [downcast(c) for c in getinoutypes(
                        trdf,
                        p,
                        t,
                        project,
                        ix,
                        dim,
                        namespace,
                        dodowncast=True
                    )]  # Tool outputs should always be downcasted
                outputs += [d]

        toollist.append({
            'id': str(t),
            'label': shorten(t),
            'inputs': inputs,
            'outputs': outputs,
            'taxonomyOperations': [t]
        })
    return {"functions": toollist}
