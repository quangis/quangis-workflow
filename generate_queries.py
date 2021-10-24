#!/usr/bin/env python3
"""
This file generates a SPARQL query for every transformation query.
"""

from transformation_algebra import TransformationQuery

from util import write_text
import queries

for name in dir(queries):
    query = getattr(queries, name)
    if not isinstance(query, TransformationQuery):
        continue

    write_text(name + ".rq", query.sparql())
