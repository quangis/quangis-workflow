from pathlib import Path
from rdflib import Graph
from quangis.namespace import CCD
from quangis.polytype import Dimension

class CoreConceptData(Graph):
    def __init__(self, path: Path):
        super().__init__()
        self.parse(path, format="ttl")
        self.dimensions = [Dimension(root, self, CCD)
            for root in [CCD.CoreConceptQ, CCD.LayerA, CCD.NominalA]
        ]


ccd = CoreConceptData(Path(__file__).parent.parent / "data" / "ccd.ttl")
