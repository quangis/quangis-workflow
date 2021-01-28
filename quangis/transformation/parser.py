"""
Functions and data structures for parsing.
"""

from __future__ import annotations

import pyparsing as pp
from functools import reduce
from typing import List, Dict, Union

from quangis.transformation.type import AlgebraType, TypeOperator, Definition


class Expr(object):
    def __init__(self, tokens: List[Union[str, Expr]], type: AlgebraType):
        self.tokens = tokens
        self.type = type

    def __str__(self) -> str:
        if self.type.is_function():
            return "{}".format(" ".join(map(str, self.tokens)))
        else:
            return "({tokens} : \033[1m{type}\033[0m)".format(
                tokens=" ".join(map(str, self.tokens)),
                type=str(self.type)
            )

    @staticmethod
    def apply(fn: Expr, arg: Expr) -> Expr:
        if isinstance(fn.type, TypeOperator):
            res = Expr([fn, arg], fn.type.apply(arg.type))
            fn.type = fn.type.instantiate()
            arg.type = arg.type.instantiate()
            return res
        else:
            raise RuntimeError("applying to non-function value")


def make_parser(defs: Dict[str, Definition]) -> pp.Parser:

    identifier = pp.Word(pp.alphas + '_', pp.alphanums + ':_').setName('identifier')

    fn = pp.MatchFirst(
        pp.CaselessKeyword(k) + t.data * identifier
        if t.data else
        pp.CaselessKeyword(k)
        for k, t in sorted(defs.items())
    ).setParseAction(lambda s, l, t: Expr(t, defs[t[0]].instance()))

    return pp.infixNotation(
        fn,
        [(None, 2, pp.opAssoc.LEFT, lambda s, l, t: reduce(Expr.apply, t[0]))]
    )
