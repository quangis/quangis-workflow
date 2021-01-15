import unittest

from quangis.namespace import EM, CCD
from quangis.semtype import project
from quangis.ontology import Ontology


class TestProjection(unittest.TestCase):

    def test_projection(self):
        """
        To test the correctness of the class projection based on a list of
        examples. More of an integration test, I suppose.
        """

        dimensions = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]

        taxonomy = Ontology.from_rdf('CoreConceptData.rdf')

        testnodes = [
            CCD.ExistenceRaster, CCD.RasterA, CCD.FieldRaster,
            CCD.ExistenceVector, CCD.PointMeasures, CCD.LineMeasures,
            CCD.Contour, CCD.Coverage, CCD.ObjectVector, CCD.ObjectPoint,
            CCD.ObjectLine, CCD.ObjectRegion, CCD.Lattice, CCD.ExtLattice
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
            CCD.BooleanA, None, None, CCD.BooleanA, None, None, CCD.OrdinalA,
            None, None, None, None, None, None, EM.ERA
        ]
        projection = project(taxonomy, dimensions)

        for ix, node in enumerate(testnodes):
            p = projection.get(node)
            self.assertEqual(p[CCD.CoreConceptQ], correctCC[ix])
            self.assertEqual(p[CCD.LayerA], correctLayerA[ix])
            self.assertEqual(p[CCD.NominalA], correctNominalA[ix])


if __name__ == '__main__':
    unittest.main()
