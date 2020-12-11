# -*- coding: utf-8 -*-
"""
Takes an RDF based specification of tools with typed inputs and outputs and
turns it into an tool description in JSON according to the APE format

@author: Schei008
@date: 2019-03-22
@copyright: (c) Schei008 2019
@license: MIT
"""

from rdf_namespaces import TOOLS, WF, CCD

from rdflib.namespace import RDF
import os
import logging


def setprefixes(g):
    g.bind('foaf', 'http://xmlns.com/foaf/0.1/')
    g.bind('ccd', 'http://geographicknowledge.de/vocab/CoreConceptData.rdf#')
    g.bind('owl', 'http://www.w3.org/2002/07/owl#')
    g.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    g.bind('xml', 'http://www.w3.org/XML/1998/namespace')
    g.bind('xsd', 'http://www.w3.org/2001/XMLSchema#')
    g.bind('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
    g.bind('em', 'http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#')
    g.bind('ada', 'http://geographicknowledge.de/vocab/AnalysisData.rdf#')
    g.bind('wf', 'http://geographicknowledge.de/vocab/Workflow.rdf#')
    g.bind('gis', 'http://geographicknowledge.de/vocab/GISConcepts.rdf#')
    g.bind('tools', 'http://geographicknowledge.de/vocab/GISTools.rdf#')
    return g


def shortURInames(URI, shortenURIs=True):
    if shortenURIs:
        if "#" in URI:
            return URI.split('#')[1]
        else:
            return os.path.basename(os.path.splitext(URI)[0])
    else:
        return URI


def getinoutypes(g,
                 predicate,
                 subject,
                 project,
                 dimix,
                 dim,
                 mainprefix,
                 dodowncast=False):
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
    if dodowncast:
        # Downcast is used to enforce leaf nodes for types. Is used to make
        # annotations as specific as possible, used only for output nodes
        outputtypes = [downcast(t) for t in outputtypes]
    out = [
        shortURInames(t) if str(mainprefix) in t else t for t in outputtypes
    ]
    # In case there is no type, just use the highest level type of the
    # corresponding dimension
    if out == []:
        if dodowncast:
            out = [shortURInames(downcast(dim))]
        else:
            out = [shortURInames(dim)]
    return out


def rdf2ape(trdf, project, dimnodes, mainprefix=CCD):
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    logging.info("Converting RDF tool annotations to APE format...")
    toollist = []
    trdf = setprefixes(trdf)
    for t in trdf.objects(None, TOOLS.implements):
        inputs = []
        for p in [WF.input1, WF.input2, WF.input3]:
            if trdf.value(subject=t, predicate=p, default=None) is not None:
                d = {}
                for ix, dim in enumerate(dimnodes):
                    d[shortURInames(dim)] = getinoutypes(
                        trdf, p, t, project, ix, dim, mainprefix)
                inputs += [d]
        outputs = []
        for p in [WF.output, WF.output2, WF.output3]:
            if trdf.value(subject=t, predicate=p, default=None) is not None:
                d = {}
                for ix, dim in enumerate(dimnodes):
                    d[shortURInames(dim)] = getinoutypes(
                        trdf,
                        p,
                        t,
                        project,
                        ix,
                        dim,
                        mainprefix,
                        dodowncast=True
                    )  # Tool outputs should always be downcasted
                outputs += [d]

        toollist.append({
            'id': t,
            'label': shortURInames(t),
            'inputs': inputs,
            'outputs': outputs,
            'taxonomyOperations': [t]
        })
        logging.debug("Adding tool {}".format(t))
    return {"functions": toollist}


def downcast(node):
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
