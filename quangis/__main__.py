"""
Generate workflows using APE with the CCD type taxonomy and the GIS tool
ontology.
"""

import json
from pathlib import Path
from rdflib import Graph
from itertools import product
from cct import cct
from transformation_algebra.util.common import build_transformation

from quangis.namespace import CCD
from quangis.wfsyn import CCDWorkflowSynthesis
from quangis.util import get_data, download_if_missing, shorten

data_dir = Path(__file__).parent.parent / "data"

tools_file = download_if_missing(
    path=data_dir / "ToolDescription.ttl",
    url="https://raw.githubusercontent.com/simonscheider/QuAnGIS/master/ToolRepository/ToolDescription.ttl"
    # url="https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl"
)

types_file = download_if_missing(
    path=data_dir / "CoreConceptData.rdf",
    url="http://geographicknowledge.de/vocab/CoreConceptData.rdf"
)

types = Graph()
types.parse(types_file, format='xml')
tools = Graph()
tools.parse(tools_file, format='ttl')

dimensions = [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]

print("Starting APE")
wfsyn = CCDWorkflowSynthesis(ccd_types=types, tools=tools,
    dimensions=dimensions)
print("Started APE")

# for d in wfsyn.dimensions:
#     d.serialize(f"{shorten(d.root)}.ttl", format="ttl")

with open("ape-tools.json", 'w') as f:
    json.dump(wfsyn.ape_tools(), f)
wfsyn.ape_type_taxonomy().serialize("ape-taxonomy.ttl", format="ttl")

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
        print("Building transformation graph...")
        g = build_transformation(cct, tools, solution)
        print(g.serialize(format="ttl"))
        g.serialize(f"solution{shorten(solution.root)}.ttl", format="ttl")
    print("Running total: {}".format(running_total))
