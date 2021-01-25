"""
Functions and data structures for parsing.
"""

from __future__ import annotations

import pyparsing as pp
from functools import reduce
from typing import List, Dict, Union

from quangis.cct.type import AlgebraType, Transformation


class Expr(object):
    def __init__(self, tokens: List[Union[str, Expr]], type: AlgebraType):
        self.tokens = tokens
        self.type = type

    def __str__(self) -> str:
        if isinstance(self.type, Transformation):
            return "{}".format(" ".join(map(str, self.tokens)))
        else:
            return "({tokens} : \033[1m{type}\033[0m)".format(
                tokens=" ".join(map(str, self.tokens)),
                type=str(self.type)
            )

    @staticmethod
    def apply(fn: Expr, arg: Expr) -> Expr:
        return Expr([fn, arg], fn.type.apply(arg.type))


def make_parser(
        constructors: Dict[str, AlgebraType],
        functions: Dict[str, AlgebraType]) -> pp.Parser:

    cons_keywords = [pp.Keyword(t) for t in sorted(constructors.keys())]

    func_keywords = [pp.Keyword(t) for t in sorted(functions.keys())]

    identifier = pp.Word(pp.alphas, pp.alphanums)

    constructor = (
        pp.MatchFirst(cons_keywords) + identifier
    ).setParseAction(
        lambda s, l, t: Expr(t, constructors[t[0]].fresh())
    )

    function = (
        pp.MatchFirst(func_keywords)
    ).setParseAction(
        lambda s, l, t: Expr(t, functions[t[0]].fresh())
    )

    return pp.infixNotation(
        constructor | function,
        [(None, 2, pp.opAssoc.LEFT, lambda s, l, t: reduce(Expr.apply, t[0]))]
    )
