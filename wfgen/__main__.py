"""
Generate workflows using APE with the CCD type taxonomy and the GIS tool
ontology.
"""

from rdflib import Graph, RDFS, Literal
from typing import Iterator
from cct import cct
from transformation_algebra.graph import TransformationGraph
from transformation_algebra.workflow import WorkflowGraph

from wfgen.namespace import CCD, EM
from wfgen.generator import WorkflowGenerator
from wfgen.util import build_dir
from wfgen.types import Type, Dimension

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


def generate_io(dimensions: list[Dimension]) \
        -> Iterator[tuple[list[Type], list[Type]]]:
    """
    To start with, we generate workflows with two inputs and one output, of
    which one input is drawn from the following sources, and the other is the
    same as the output without the measurement level.
    """
    for goal_tuple in goals:
        goal = Type(dimensions, goal_tuple)
        source1 = Type(goal)
        source1[CCD.NominalA] = {CCD.NominalA}
        for source_tuple in sources:
            source2 = Type(dimensions, source_tuple)
            yield [source1, source2], [goal]


print("Starting APE")
gen = WorkflowGenerator()

print("Produce dimension trees")
for d in gen.dimensions:
    name = str(d.root).split("#")[1]
    d.serialize(build_dir / f"dimension-{name}.ttl", format="ttl")

running_total = 0
for inputs, outputs in generate_io(gen.dimensions):
    print("Generating workflows for:", inputs, "->", outputs)
    for solution in gen.run(inputs, outputs, solutions=1):
        running_total += 1
        print("Found a solution; building transformation graph...")
        wf: Graph
        try:
            wf = WorkflowGraph(cct, gen.tools)
            wf += solution
            wf.refresh()
            wf_enriched = TransformationGraph(cct)
            wf_enriched.add_workflow(wf)
            wf_enriched += solution
            success = True
        # TODO transformation-algebra-specific errors
        except Exception as e:
            success = False
            print(f"Could not construct transformation graph: {e}")
            wf_enriched.add((solution.root, RDFS.comment,
                Literal(f"could not construct transformation graph: {e}")))

        name = f"solution-{running_total}{'' if success else '-error'}"
        wf_enriched.serialize(build_dir / (name + ".ttl"), format="ttl")
        wf_enriched.visualize(build_dir / (name + ".dot"))
    print("Running total: {}".format(running_total))
