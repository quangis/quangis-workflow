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
from rdf_namespaces import TOOLS, WF, CCD

from rdflib.namespace import RDF
import os
import logging
import subprocess
import tempfile
import json
from six.moves.urllib.parse import urldefrag


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


def tool_annotations(trdf, project, dimnodes, mainprefix=CCD):
    """
    Project tool annotations with the projection function, convert it to a
    dictionary that APE understands
    """

    logging.info("Converting RDF tool annotations to APE format...")
    toollist = []
    trdf = rdf_namespaces.setprefixes(trdf)
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


def frag(node):
    return urldefrag(node).fragment


def prepare_io(entries):
    """
    Transform input and outputs specifications to the format expected by APE.
    """

    return [
            {
                frag(dimension):
                    [frag(c) for c in ontology_class]
                    if type(ontology_class) == list else
                    [frag(ontology_class)]
                for dimension, ontology_class in entry.items()
            }
            for entry in entries
        ]


def configuration(
        output_directory,
        ontology_path,
        tool_annotations_path,
        dimensions,
        inputs,
        outputs):
    """
    Prepare a dictionary containing APE configuration.
    """

    return {
        "solutions_dir_path": output_directory,
        "ontology_path": ontology_path,
        "tool_annotations_path": tool_annotations_path,
        "constraints_path": os.path.join(output_directory, "..", "data", "constraints.json"),
        "ontologyPrexifIRI": "http://geographicknowledge.de/vocab/"
                             "CoreConceptData.rdf#",
        "toolsTaxonomyRoot": "http://geographicknowledge.de/vocab/"
                             "GISTools.rdf#Tool",
        "dataDimensionsTaxonomyRoots": [frag(iri) for iri in dimensions],
        "shared_memory": "true",
        "solution_length": {"min": 1, "max": 10},
        "max_solutions": "5",
        "number_of_execution_scripts": "0",
        "number_of_generated_graphs": "0",
        "inputs": prepare_io(inputs),
        "outputs": prepare_io(outputs),
        "debug_mode": "false",
        "use_workflow_input": "all",
        "use_all_generated_data": "all",
        "tool_seq_repeat": "false"
    }


def run(executable, configuration):
    """
    Run APE.

    @param executable: Path to APE jar-file.
    @param configuration: Dictionary representing APE configuration object.
    """

    tmp = tempfile.mkdtemp(prefix="ape-")
    config_path = os.path.join(tmp, "ape.config")
    with open(config_path, 'w') as f:
        json.dump(configuration, f)
    subprocess.call(["java", "-jar", executable, config_path])
    os.remove(config_path)
    os.rmdir(tmp)

