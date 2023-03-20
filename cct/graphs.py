from rdflib import Graph
from pathlib import Path

root = Path(__file__).parent.parent
tools = Graph()
tools.parse(root / "tools" / "tools.ttl")
