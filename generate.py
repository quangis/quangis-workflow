#!/usr/bin/env python3
"""
Generate workflows using APE with the CCD type taxonomy and the GIS tool
ontology.
"""

from pathlib import Path
from wfgen.namespace import CCD, EM, EX
from wfgen.generator import WorkflowGenerator
from wfgen.types import Type
from transformation_algebra.namespace import shorten

sources = [
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.PlainNominalA),  # VectorCoverage
    (CCD.FieldQ, CCD.VectorTessellationA, CCD.PlainOrdinalA),  # Contour
    (CCD.FieldQ, CCD.PointA, CCD.PlainIntervalA),  # PointMeasures
    (CCD.FieldQ, CCD.PointA, CCD.PlainRatioA),  # PointMeasures
    (CCD.FieldQ, CCD.LineA, CCD.PlainIntervalA),  # LineMeasures (isolines)
    (CCD.FieldQ, CCD.LineA, CCD.PlainRatioA),  # LineMeasures (isolines)
    (CCD.FieldQ, CCD.PlainVectorRegionA, CCD.PlainNominalA),  # Patch
    (CCD.FieldQ, CCD.RasterA, CCD.PlainIntervalA),  # Field Raster
    (CCD.FieldQ, CCD.RasterA, CCD.PlainRatioA),  # Field Raster

    # Commented out because there are actually no tools which accept this
    # input, which makes APE very very mad.
    # (CCD.AmountQ, CCD.RasterA, CCD.CountA),  # Count Raster
    # (CCD.AmountQ, CCD.PlainVectorRegionA, CCD.CountA),  # Count Vector
    # (CCD.AmountQ, CCD.PointA, CCD.CountA),  # Count Vector

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


def generate_workflows():
    build_dir = Path(__file__).parent / "build"
    gen = WorkflowGenerator(build_dir)

    # To start with, we generate workflows with two inputs and one output, of
    # which one input is drawn from the following sources, and the other is the
    # same as the output without the measurement level.
    inputs_outputs: list[tuple[str, list[Type], list[Type]]] = []
    for goal_tuple in goals:
        goal = Type(gen.dimensions, goal_tuple)
        goal_str = "+".join(shorten(g) for g in goal_tuple)
        source1 = Type(goal)
        source1[CCD.NominalA] = {CCD.NominalA}
        for source_tuple in sources:
            source2 = Type(gen.dimensions, source_tuple)
            source_str = "+".join(shorten(s) for s in source_tuple)
            inputs_outputs.append((f"{source_str}_{goal_str}_",
                [source1, source2], [goal]))

    running_total = 0
    for run, (name, inputs, outputs) in enumerate(inputs_outputs):
        for solution in gen.run(inputs, outputs, solutions=1, prefix=EX[name]):
            running_total += 1
            path = build_dir / f"{shorten(solution.root)}.ttl"
            print(f"Writing solution: {path}")
            solution.serialize(path, format="ttl")


if __name__ == "__main__":
    generate_workflows()
