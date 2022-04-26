import importlib
import importlib.machinery
import importlib.util
from typing import TypedDict
from rdflib.term import Node
from transformation_algebra import Query
from pathlib import Path


class QueryVariant(TypedDict):
    """
    Query annotated with its name, expected results and variants.
    """
    name: str
    expected: set[Node]
    variants: dict[str, Query]


def from_python(path: Path) -> QueryVariant:
    """
    Load queries from Python file.
    """
    name = path.stem
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)

    return {
        "name": name,
        "expected": getattr(module, 'workflows'),
        "variants": {
            variant: query
            for variant in dir(module)
            if isinstance(query := getattr(module, variant), Query)
        }
    }


all_queries = [from_python(p)
    for p in Path(__file__).parent.glob("*.py")
    if not p.name.startswith("__")
]

all_workflows: list[Node] = list(
    set.union(*(q["expected"] for q in all_queries))
)
