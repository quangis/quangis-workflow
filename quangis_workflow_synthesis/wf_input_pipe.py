# -*- coding: utf-8 -*-
"""
Generates input data for workflow generator (APE) from a given OWL data
ontology and a given tool annotation file, by projecting classes to ontology
dimensions.

@author: Schei008
@date: 2020-04-08
@copyright: (c) Schei008 2020
@license: MIT
"""

from rdfnamespaces import CCD
import wf_taxonomy_cleaner
import tool_annotator
import semdim_projector

import rdflib
import os


def ontology(path):
    """
    Load an RDF graph from a file.
    """
    g = rdflib.Graph()
    g.parse(path, format="turtle")
    return g

# dto is used multiple times. I just need to check if that doesn't cause
# cloning issues

def pipe(ontology_tool, ontology_ccd,
         targetfolder='/mnt/c/Users/3689700/repo/QuAnGIS_Simon/WorkflowSynthesis/flowmap'):

    dimnodes = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
    dimnodes_fl = [CCD.DType]
    dimnodes_flgraph = [CCD.CoreConceptQ, CCD.LayerA]

    # 1) Generates a taxonomy (_tax) version of the ontology as well as of the
    # given tool hierarchy (using rdfs:subClassOf), by applying reasoning and
    # removing all other statements
    # name, ext = os.path.splitext(tooldescfile)
    # to = os.path.join(targetfolder,
    #                  name + "_tax" + ext)  # to='ToolDescription_tax.ttl'
    # name, ext = os.path.splitext(os.path.basename(ontologyfile))
    # dto = os.path.join(targetfolder,
    #                   name + "_tax" + ext)  # dto = 'CoreConceptData_tax.ttl'
    # wf_taxonomy_cleaner.main(ontologyfile=ontologyfile, tooldesc=tooldescfile, to=to, dto=dto)
    to = wf_taxonomy_cleaner.cleanOWLOntology(ontology_ccd)
    dto = wf_taxonomy_cleaner.extractToolOntology(ontology_tool)

    # 2) Computes a projection of classes to any of a given set of dimensions given by superconcepts in the type taxonomy file
    # tax, ext = os.path.splitext(os.path.basename(dto))
    # coretax = os.path.join(targetfolder, tax + '_core' +
    #                       ext)  # 'CoreConceptData_tax_core.ttl'
    # Generates a file 'CoreConceptData_tax_core.ttl' which contains the ontology cleaned from non-core nodes (=not belonging to the core of a dimension)
    # coretax = semdim_projector.main(taxonomy=dto, dimnodes=dimnodes)
    # print(project)
    # Does the same for the flattened version
    #coretax_fl = os.path.join(targetfolder, tax + '_core_flgraph' +
    #                          ext)  # 'CoreConceptData_tax_core.ttl'
    coretax_fl = semdim_projector.main(taxonomy=dto, dimnodes=dimnodes_flgraph)

    # 3) Generates a single ontology (of tool_tax + type_tax), and generates a
    # new new tool annotation file (json) with the projected classes as input
    # for APE
    # final = rdflib.Graph()
    # final.parse(os.path.join(targetfolder,coretax), format='turtle')
    # final.parse(os.path.join(targetfolder,to), format='turtle')
    # final.serialize(destination=os.path.join(targetfolder, 'GISTaxonomy.rdf'), format = "application/rdf+xml")
    # Then generates a JSON version of the tooldescription for the full taxonomy (to be used with GISTaxonomy.rdf)
    # Generates a new json file "ToolDescription.json" in the targetfolder to be used as APE input
    # toolannotator.main(tooldescfile, project, dimnodes, mainprefix=CCD, targetfolder=targetfolder)

    final = rdflib.Graph()
    final += coretax_fl
    final += to

    # final.parse(os.path.join(targetfolder, coretax_fl), format='turtle')
    # final.parse(os.path.join(targetfolder, to), format='turtle')
    final.serialize(destination=os.path.join(targetfolder, 'GISTaxonomy_flgraph.rdf'), format="application/rdf+xml")

    # tooldescfile_fl = ontology('/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription_fl.ttl')
    tooldescfile_flgraph = ontology('/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription_flgraph.ttl')

    tool_annotator.main(tooldescfile_flgraph,
                        coretax_fl,
                        dimnodes_flgraph,
                        mainprefix=CCD,
                        targetpath=os.path.join(targetfolder,"FlowmapDescription_flgraph.json"))


def main():
    pipe(ontology_tool=ontology("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/ToolRepository/FlowmapDescription.ttl"),
         ontology_ccd=ontology("/mnt/c/Users/3689700/repo/QuAnGIS_Simon/Ontology/CoreConceptData.ttl"))


if __name__ == '__main__':
    main()
