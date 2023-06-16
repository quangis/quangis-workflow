import unittest

from quangis.namespace import CCD
from quangis.ccd import ccd
from quangis.polytype import Polytype
from rdflib.namespace import Namespace

EM = Namespace('http://geographicknowledge.de/vocab/ExtensiveMeasures.rdf#')

class TestProjection(unittest.TestCase):

    def test_projection(self):
        """Test the correctness of the class projection based on a list of
        examples."""

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
            with self.subTest(f"{node}"):
                p = Polytype.project(ccd.dimensions, [node])
                self.assertEqual(p[CCD.CoreConceptQ],
                    set(correctCC[ix]) or {CCD.CoreConceptQ})
                self.assertEqual(p[CCD.LayerA],
                    set(correctLayerA[ix]) or {CCD.LayerA})
                self.assertEqual(p[CCD.NominalA],
                    set(correctNominalA[ix]) or {CCD.NominalA})


if __name__ == '__main__':
    unittest.main()
