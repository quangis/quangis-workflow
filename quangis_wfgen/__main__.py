"""
Generate workflows using APE with the CCD type taxonomy and the GIS tool
ontology.
"""

from typing import Iterator
# from cct import cct
# from transformation_algebra.util.common import build_transformation

from quangis_wfgen.namespace import CCD, EM
from quangis_wfgen.wfsyn import CCDWorkflowSynthesis
from quangis_wfgen.util import download_if_missing, build_dir
from quangis_wfgen.dimtypes import DimTypes, Dimension

tools = download_if_missing(build_dir / "ToolDescription.ttl",
    "https://raw.githubusercontent.com/simonscheider/QuAnGIS/master/"
    "ToolRepository/ToolDescription.ttl")

types = download_if_missing(build_dir / "CoreConceptData.rdf",
    "http://geographicknowledge.de/vocab/CoreConceptData.rdf")

dimension_roots = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
sources = [
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.PlainNominalA),  # Vector Coverage
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.PlainOrdinalA),  # Contour
    (CCD.FieldQ, CCD.PointA, CCD.PlainIntervalA),  # PointMeasures
    (CCD.FieldQ, CCD.PointA, CCD.PlainRatioA),  # PointMeasures
    (CCD.FieldQ, CCD.LineA, CCD.PlainIntervalA),  # LineMeasures (isolines)
    (CCD.FieldQ, CCD.LineA, CCD.PlainRatioA),  # LineMeasures (isolines)
    (CCD.FieldQ, CCD.PlainVectorRegionA, CCD.PlainNominalA),  # Patch
    (CCD.FieldQ, CCD.RasterA, CCD.PlainIntervalA),  # Field Raster
    (CCD.FieldQ, CCD.RasterA, CCD.PlainRatioA),  # Field Raster

    (CCD.AmountQ, CCD.RasterA, CCD.CountA),  # Count Raster
    (CCD.AmountQ, CCD.PlainVectorRegionA, CCD.CountA),  # Count Vector
    (CCD.AmountQ, CCD.PointA, CCD.CountA),  # Count Vector

    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.PlainNominalA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.PlainOrdinalA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.PlainIntervalA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, EM.ERA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, EM.IRA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.PlainRatioA),  # Lattice
    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.CountA),  # Lattice

    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.PlainNominalA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.PlainOrdinalA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.PlainIntervalA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, EM.ERA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, EM.IRA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.PlainRatioA),  # ObjectRegion
    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.CountA),  # ObjectRegion

    (CCD.ObjectQ, CCD.PointA, CCD.PlainNominalA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, CCD.PlainOrdinalA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, CCD.PlainIntervalA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, EM.ERA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, EM.IRA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, CCD.PlainRatioA),  # ObjectPoint
    (CCD.ObjectQ, CCD.PointA, CCD.CountA),  # ObjectPoint
]
goals = [
    (CCD.FieldQ, CCD.PlainVectorRegionA, CCD.NominalA),
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.NominalA),
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.OrdinalA),
    (CCD.FieldQ, CCD.RasterA, CCD.IntervalA),
    (CCD.FieldQ, CCD.RasterA, CCD.RatioA),

    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.IntervalA),
    (CCD.ObjectQ, CCD.VectorTessellationA, EM.ERA),
    (CCD.ObjectQ, CCD.VectorTessellationA, EM.IRA),
    (CCD.ObjectQ, CCD.VectorTessellationA, CCD.CountA),

    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.IntervalA),
    (CCD.ObjectQ, CCD.PlainVectorRegionA, EM.ERA),
    (CCD.ObjectQ, CCD.PlainVectorRegionA, EM.IRA),
    (CCD.ObjectQ, CCD.PlainVectorRegionA, CCD.CountA),
]


def generate_io(dimensions: list[Dimension]) \
        -> Iterator[tuple[list[DimTypes], list[DimTypes]]]:
    """
    To start with, we generate workflows with two inputs and one output, of
    which one input is drawn from the following sources, and the other is the
    same as the output without the measurement level.
    """
    for goal_tuple in goals:
        goal = DimTypes(dimensions, goal_tuple)
        source1 = DimTypes(goal)
        source1[CCD.NominalA] = {CCD.NominalA}
        for source_tuple in sources:
            source2 = DimTypes(dimensions, source_tuple)
            yield [source1, source2], [goal]


print("Starting APE")
wfsyn = CCDWorkflowSynthesis(types=types, tools=tools,
    dimension_roots=dimension_roots)
print("Started APE")

running_total = 0
for inputs, outputs in generate_io(wfsyn.dimensions):
    solutions = wfsyn.run(inputs=inputs, outputs=outputs, solutions=1)
    for solution in solutions:
        running_total += 1
        solution.serialize(build_dir / f"solution{running_total}.ttl",
            format="ttl")
        # print("Building transformation graph...")
        # g = build_transformation(cct, tools, solution)
        # print(g.serialize(format="ttl"))
        # g.serialize(f"solution{shorten(solution.root)}.ttl", format="ttl")
    print("Running total: {}".format(running_total))
