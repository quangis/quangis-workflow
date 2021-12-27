#!/usr/bin/env python3
"""
"""

import sys
from pathlib import Path
import importlib.machinery
import importlib.util

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
                print(name, variant)
                result[name, variant] = query
    return result


extract_queries()
