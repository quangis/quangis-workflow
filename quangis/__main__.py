"""
Generate workflows using APE with the CCD type taxonomy and the GIS tool
ontology.
"""

from pathlib import Path
from rdflib import Graph
from itertools import product
# from cct import cct
# from transformation_algebra.util.common import build_transformation

from quangis.namespace import CCD
from quangis.wfsyn import CCDWorkflowSynthesis
from quangis.util import get_data, download_if_missing, build_dir

data_dir = Path(__file__).parent.parent / "data"

tools_file = download_if_missing(build_dir / "ToolDescription.ttl",
    "https://raw.githubusercontent.com/simonscheider/QuAnGIS/master/"
    "ToolRepository/ToolDescription.ttl")
    # "https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl"

types_file = download_if_missing(build_dir / "CoreConceptData.rdf",
    "http://geographicknowledge.de/vocab/CoreConceptData.rdf")

types = Graph()
types.parse(types_file, format='xml')
tools = Graph()
tools.parse(tools_file, format='ttl')

dimensions = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]

print("Starting APE")
wfsyn = CCDWorkflowSynthesis(ccd_types=types, tools=tools,
    dimensions=dimensions)
print("Started APE")

inputs = get_data(data_dir / "sources.txt", wfsyn.dimensions)
outputs = get_data(data_dir / "goals.txt", wfsyn.dimensions)

running_total = 0
for i, o in product(inputs, outputs):
    print("Running synthesis for {} -> {}".format(i, o))

    solutions = wfsyn.run(
        inputs=[i],
        outputs=[o],
        solutions=1)
    for solution in solutions:
        running_total += 1
        solution.serialize(build_dir / f"solution{running_total}.ttl",
            format="ttl")
        # print("Building transformation graph...")
        # g = build_transformation(cct, tools, solution)
        # print(g.serialize(format="ttl"))
        # g.serialize(f"solution{shorten(solution.root)}.ttl", format="ttl")
    print("Running total: {}".format(running_total))
