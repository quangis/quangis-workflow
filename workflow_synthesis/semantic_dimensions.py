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

from rdf_namespaces import CCD, EXM

import rdflib
from rdflib.namespace import RDFS
import os
import logging
from rdflib import Graph, URIRef
from rdflib.term import Node
from typing import Iterable, List, Mapping

from taxonomy import Taxonomy

CORE = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
FLAT = [CCD.DType]
FLATGRAPH = [CCD.CoreConceptQ, CCD.LayerA]


class SubsumptionTree(Taxonomy):
    def __init__(self, root, *args, **kwargs):
        self.root = root
        super(*args, **kwargs)


def subsumption_tree(g: Taxonomy, root: Node) -> SubsumptionTree:
    """
    This method takes a taxonomy (a graph of raw subsumption relations) and an
    arbitrary root and generates a tree with unique parent relations towards
    the root for each node.
    """

    # Get a (root, [(child1, [...])]) structure
    tree = rdflib.util.get_tree(g, root, RDFS.subClassOf)

    t = SubsumptionTree(root)

    def f(r, *nodes):
        for n in nodes:
            t.add((n, RDFS.subClassOf, r))

    return f(root, tree)



def dimcore(n, parent, idxc, listoftrees):
    """
    Determines whether a given node is at the core of a dimension, that is, not
    subsumed by any other dimension.
    """
    out = True
    for idx, tree in enumerate(listoftrees):
        if idx != idxc:
            distance = tree[0]
            if n in distance.keys():
                out = False
                break
    return out


def project(taxonomy: Taxonomy, dimensions: List[URIRef]):
    """
    This method takes some (subsumption) taxonomy and a list of supertypes for
    each dimension. It constructs a tree for each dimension and returns a
    projection of all nodes that intersect with one of these dimensions into
    the core of the dimension. It also generates a corresponding core taxonomy
    (containing only core classes for each dimension).
    """

    leaves = taxonomy.leaves()
    subsumptions = [subsumption_tree(taxonomy, d) for d in dimensions]

    (projection, notcore) = project2Dimensions(nodes, subsumptions)
    return (core_taxonomy(taxonomy, notcore), projection)


def project2Dimensions(
        nodes: Iterable[Node],
        subsumptions: Iterable[SubsumptionTree]) -> Mapping[Node, Node]:
    """
    This method projects given nodes to all dimensions given as a list of
    dimensions (as subsumption trees). Any node that is subsumed by at least
    one tree can be projected to the closest parent in that tree which belongs
    to its core. If a node cannot be projected to a given dimension, then
    project maps to None.
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
    project = {k: v for k, v in project.items() if v}

    return project



