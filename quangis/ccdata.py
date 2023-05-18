from pathlib import Path
from rdflib import Graph
from quangis.namespace import CCD
from quangis.polytype import Dimension

ccd_file = Path(__file__).parent.parent / "data" / "ccd.ttl"
ccd_graph = Graph()
ccd_graph.parse(ccd_file, format="ttl")

dimensions = [Dimension(root, ccd_graph, CCD)
    for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
]
