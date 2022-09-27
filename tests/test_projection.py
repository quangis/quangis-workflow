import unittest

from rdflib import Graph
from quangis.namespace import EM, CCD
from quangis.semtype import SemType, Dimension


class TestProjection(unittest.TestCase):

    def test_projection(self):
        """
        To test the correctness of the class projection based on a list of
        examples.
        """

        ccd = Graph()
        ccd.parse('CoreConceptData.rdf', format='xml')

        dimensions = [
            Dimension(root, source=ccd)
            for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
        ]

        testnodes = [
            CCD.ExistenceRaster, CCD.RasterA, CCD.FieldRaster,
            CCD.ExistenceVector, CCD.PointMeasures, CCD.LineMeasures,
            CCD.Contour, CCD.Coverage, CCD.ObjectVector, CCD.ObjectPoint,
            CCD.ObjectLine, CCD.ObjectRegion, CCD.Lattice, CCD.ExtLattice
        ]
        correctCC = [
            [CCD.FieldQ], [], [CCD.FieldQ], [CCD.FieldQ], [CCD.FieldQ],
            [CCD.FieldQ], [CCD.FieldQ], [CCD.FieldQ], [CCD.ObjectQ],
            [CCD.ObjectQ], [CCD.ObjectQ], [CCD.ObjectQ], [CCD.ObjectQ],
            [CCD.ObjectQ]
        ]
        correctLayerA = [
            [CCD.RasterA], [CCD.RasterA], [CCD.RasterA], [CCD.VectorA],
            [CCD.PointA], [CCD.LineA], [CCD.TessellationA],
            [CCD.TessellationA], [CCD.VectorA], [CCD.PointA], [CCD.LineA],
            [CCD.RegionA], [CCD.TessellationA], [CCD.TessellationA]
        ]
        correctNominalA = [
            [CCD.BooleanA], [], [], [CCD.BooleanA], [], [], [CCD.OrdinalA],
            [], [], [], [], [], [], [EM.ERA]
        ]

        for ix, node in enumerate(testnodes):
            p = SemType.project(dimensions, [node])
            self.assertEqual(p[CCD.CoreConceptQ], set(correctCC[ix]))
            self.assertEqual(p[CCD.LayerA], set(correctLayerA[ix]))
            self.assertEqual(p[CCD.NominalA], set(correctNominalA[ix]))


if __name__ == '__main__':
    unittest.main()
