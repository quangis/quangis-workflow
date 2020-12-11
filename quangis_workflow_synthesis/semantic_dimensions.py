# -*- coding: utf-8 -*-
"""
These methods are used to construct semantic dimensions (subsumption trees) for
a given list of superconcepts that identify these dimensions. It returns a
projection function which projects any subsumed node to all given dimensions.
None is returned if the node cannot be projected to this dimension. The method
is used to clean annotations such that we can represent them as a conjunction
of concepts from different semantic dimensions.

Note: Internally, the method turns a subsumption DAG into a tree
(getSubsumptionTree). Since this is in general non-unique (see Topological
ordering of a DAG), the method is deterministic only when the subsumption graph
is in its raw form (similar to a tree). It should not be used on subsumption
graphs that were closed with reasoning. The graph needs to contain a minimal
set of subsumption relations.

@author: Schei008
@date: 2020-04-08
@copyright: (c) Schei008 2020
@license: MIT
"""

from rdf_namespaces import CCD, EXT

import rdflib
from rdflib.namespace import RDFS
import os
import logging

CORE = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
FLAT = [CCD.DType]
FLATGRAPH = [CCD.CoreConceptQ, CCD.LayerA]


def getSubsumptionTree2(g, root, leafnodes):
    """
    This method takes a taxonomy (a graph of raw subsumption relations) and an
    arbitrary root and generates a tree with unique parent relations towards
    the root for each node. Uses rdflib's built in get_tree. Note: not unique!
    """

    logging.debug("Root node: {}".format(root))
    tuplelisttree = rdflib.util.get_tree(g, root, RDFS.subClassOf)
    distance = {}
    parent = {}
    visitednodes = set()

    count = 0
    tuple = tuplelisttree
    traverse(tuple, count, distance, parent, visitednodes)

    logging.debug("Size of tree: {}".format(len(distance.keys())))
    logging.debug("Depth of tree: {}".format(max(distance.values())))
    for n in leafnodes.intersection(visitednodes):
        logging.debug(distance[n])
        logging.debug(n)
        backtrack(parent, n)
    return (distance, parent)


def traverse(tuple, count, distance, parent, visitednodes):
    current = tuple[0]
    distance[current] = count
    visitednodes.add(current)
    for child in tuple[1]:
        parent[child[0]] = current
        traverse(child, count + 1, distance, parent, visitednodes)


def backtrack(parent, leaf):
    node = leaf
    while node in parent.keys() and node is not None:
        node = parent[node]
        logging.debug(node)


def measureTaxonomy(g):
    """
    Measures the size of a taxonomy's set of nodes and determines the leafnodes
    """

    leafnodes = set()
    nodes = list(g.subjects(predicate=RDFS.subClassOf, object=None))
    count = 0
    for node in nodes:
        count += 1
        if not (None, RDFS.subClassOf, node) in g:
            leafnodes.add(node)
    logging.debug("size of taxonomy without roots: {}".format(count))
    return (nodes, leafnodes)


def project2Dimensions(nodes, listoftrees):
    """
    This method projects given nodes to all dimensions given as a list of
    dimensions (as subsumption trees). Any node that is subsumed by at least
    one tree can be projected to the closest parent in that tree which belongs
    to its core. The index of the list indicates the dimension. If a node
    cannot be projected to a given dimension, then project maps to None.
    """

    project = {}
    notcore = set()
    for n in nodes:
        project[n] = []
        for idx, tree in enumerate(listoftrees):
            parent = tree[1]
            distance = tree[0]
            p = None
            if n in distance.keys():
                p = n
                # p needs to belong to the core of the given dimension (tree)
                while not dimcore(p, parent, idx, listoftrees):
                    notcore.add(p)
                    p = parent[p]
            project[n].append(p)
    # remove nodes that cannot be projected in any way
    project = {key: val for key, val in project.items() if set(val) != {None}}
    return (project, notcore)


def dimcore(n, parent, idxc, listoftrees):
    """
    Determines whether a given node is at the core of a dimension (i.e. not
    subsumed by any other dimension)
    """
    out = True
    for idx, tree in enumerate(listoftrees):
        if idx != idxc:
            distance = tree[0]
            if n in distance.keys():
                out = False
                break
    return out


def shortURInames(URI):
    if URI is None:
        return None
    elif "#" in URI:
        return URI.split('#')[1]
    else:
        return os.path.basename(os.path.splitext(URI)[0])


# To test the correctness of the class projection based on a list of examples
def test(project):
    testnodes = [
        CCD.ExistenceRaster, CCD.RasterA, CCD.FieldRaster, CCD.ExistenceVector,
        CCD.PointMeasures, CCD.LineMeasures, CCD.Contour, CCD.Coverage,
        CCD.ObjectVector, CCD.ObjectPoint, CCD.ObjectLine, CCD.ObjectRegion,
        CCD.Lattice, CCD.ExtLattice
    ]
    correctCC = [
        CCD.FieldQ, None, CCD.FieldQ, CCD.FieldQ, CCD.FieldQ, CCD.FieldQ,
        CCD.FieldQ, CCD.FieldQ, CCD.ObjectQ, CCD.ObjectQ, CCD.ObjectQ,
        CCD.ObjectQ, CCD.ObjectQ, CCD.ObjectQ
    ]
    correctLayerA = [
        CCD.RasterA, CCD.RasterA, CCD.RasterA, CCD.VectorA, CCD.PointA,
        CCD.LineA, CCD.TessellationA, CCD.TessellationA, CCD.VectorA,
        CCD.PointA, CCD.LineA, CCD.RegionA, CCD.TessellationA,
        CCD.TessellationA
    ]
    correctNominalA = [
        CCD.BooleanA, None, None, CCD.BooleanA, None, None, CCD.OrdinalA, None,
        None, None, None, None, None, EXT.ERA
    ]
    for ix, n in enumerate(testnodes):
        print("Test:")
        print(shortURInames(n))
        if n in project.keys():
            pr = project[n]
            print("CC: " + str(shortURInames(pr[0])) + " should be: " +
                  str(shortURInames(correctCC[ix])))
            print("LayerA: " + str(shortURInames(pr[1])) + " should be: " +
                  str(shortURInames(correctLayerA[ix])))
            print("NominalA: " + str(shortURInames(pr[2])) + " should be: " +
                  str(shortURInames(correctNominalA[ix])))
        else:
            print("node not present!")


def getcoretaxonomy(g, notcore):
    """
    This method generates a taxonomy where nodes intersecting with more than
    one dimension (= not core) are removed. This is needed because APE should
    reason only within any of the dimensions.
    """

    outgraph = rdflib.Graph()
    for (s, p, o) in g.triples((None, RDFS.subClassOf, None)):
        if s not in notcore:
            outgraph.add((s, p, o))
    return outgraph
    # outgraph.serialize(destination=out, format='turtle')


def project(taxonomy,
            dimnodes=[CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]):
    """
    This method takes some (subsumption) taxonomy and a list of supertypes for
    each dimension. It constructs a tree for each dimension and returns a
    projection of all nodes that intersect with one of these dimensions into
    the core of the dimension. It also generates a corresponding core taxonomy
    (containing only core classes for each dimension)
    """
    (nodes, leafnodes) = measureTaxonomy(taxonomy)
    listofdimtrees = []
    for dim in dimnodes:
        listofdimtrees.append(getSubsumptionTree2(taxonomy, dim, leafnodes))
    (projection, notcore) = project2Dimensions(nodes, listofdimtrees)
    # test(projection)
    return (getcoretaxonomy(taxonomy, notcore), projection)

