#!/usr/bin/env python3
"""
"""

import sys
import importlib.machinery
import importlib.util
from pathlib import Path
from rdflib import Graph

from transformation_algebra.query import Query

project_dir = Path(__file__).parent.parent
sys.path.append(str(project_dir))


def extract_queries(query_dir: Path = project_dir / 'queries') \
        -> dict[tuple[str, str], Query]:
    """
    Extract queries defined in modules.
    """
    # Perhaps overengineered but makes it simple to add and change queries in
    # dedicated modules
    result: dict[tuple[str, str], Query] = dict()
    for fp in query_dir.iterdir():
        name = fp.stem
        if not fp.suffix == '.py':
            continue
        loader = importlib.machinery.SourceFileLoader(name, str(fp))
        spec = importlib.util.spec_from_loader(name, loader)
        assert spec
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        for variant in dir(module):
            query = getattr(module, variant)
            if isinstance(query, Query):
                result[name, variant] = query
    return result


wfgraph = Graph(store='SPARQLStore')
wfgraph.open("http://localhost:3030/name")

for (workflow, variant), query in extract_queries().items():
    if workflow != "Noise":
        continue
    print(workflow, variant)
    wfgraph.query(
        query.sparql()
    )

# result = graph.query("""
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     PREFIX ta: <https://github.com/quangis/transformation-algebra#>
#     PREFIX cct: <https://github.com/quangis/cct#>
#     SELECT ?s WHERE {?s rdf:type ta:Transformation. }
# """)

# for line in result:
#     print(line)

