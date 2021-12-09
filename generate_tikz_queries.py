#!/usr/bin/env python3
"""
Quick & dirty script to generate a LaTeX representation of queries via tikz.
"""

from __future__ import annotations

from sys import stdout
from itertools import count
from transformation_algebra.query import Query
from transformation_algebra.type import Type
from transformation_algebra.expr import Operator
from transformation_algebra.flow import Flow1, SEQ, OR, AND
import queries as queries_module

counter = count(start=1)

queries: list[tuple[str, Query]] = [
    (name, query) for name in dir(queries_module)
    if isinstance(query := getattr(queries_module, name), Query)
]


def write_flow(h, flow: Flow1[Type | Operator],
        previous: int | None = None,
        skip: bool = False,
        current: int | None = None,
        context: int | None = None) -> None:

    orOperator = isinstance(flow, OR) and all(
        isinstance(i, Operator) for i in flow.items)

    if isinstance(flow, (Type, Operator)) or orOperator:

        if context:
            mod = f", below of={context}"
        elif previous:
            mod = f", right of={previous}"
        else:
            mod = ""

        if orOperator:
            text = " /\\\\".join(i.name for i in flow.items)  # type: ignore
        else:
            text = str(flow)  # type: ignore
        text = text.replace("_", "\\_")

        h.write(f"\\node[main] ({current}) [align=left{mod}] {{{text}}};\n")

        if previous:
            h.write(f"\\draw[<-{',dash dot' if skip else ''}] ({previous}) -- ({current});\n")

    elif isinstance(flow, SEQ):
        previous = previous
        skip = skip or flow.skips[0]
        for i in range(len(flow.items)):
            write_flow(h, flow.items[i], previous, skip, current, context)
            skip = flow.skips[i + 1]
            previous = current
            current = next(counter)
            context = None

    elif isinstance(flow, (AND, OR)):
        write_flow(h, flow.items[0], previous, skip, current, context)
        context = current
        for item in flow.items[1:]:
            current = next(counter)
            write_flow(h, item, previous, skip, current, context)

    else:
        raise NotImplementedError(type(flow))


with stdout as f:
    f.write("\\documentclass{standalone}\n")
    f.write("\\usepackage{tikz}\n")
    f.write("\\begin{document}\n")

    for name, query in queries:
        f.write(f"Graph for {name}\n".replace('_', '\n'))
        f.write(
            "\\begin{tikzpicture}[node distance={30mm}, "
            "thick, main/.style = {draw, circle}]\n")
        write_flow(f, previous=None, skip=False, current=next(counter),
            flow=query.flow)
        f.write("\\end{tikzpicture}\\\\\n")
    f.write("\\end{document}\n")
