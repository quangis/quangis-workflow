#!/usr/bin/env python3
"""
This module...
"""

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
        None, None, None, None, None, EXM.ERA
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

