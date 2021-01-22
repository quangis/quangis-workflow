from __future__ import annotations

from functools import reduce
import pyparsing as pp

from type import constructors, functions, CCTType


class Expr(object):
    pass


class Atom(Expr):
    """
    Functions or values.
    """

    def __init__(self, name: str, type: CCTType):
        self.name = name
        self.type = type

    def __str__(self) -> str:
        return "atom({} : {})".format(self.name, self.type)


class App(Expr):
    """
    Function application.
    """

    def __init__(self, f: Expr, x: Expr):
        self.f = f
        self.x = x

    def __str__(self):
        return "({} {})".format(self.f, self.x)


constructor = (
    pp.MatchFirst([pp.Keyword(t) for t in constructors.keys()]) + \
    pp.Word(pp.alphas, pp.alphanums)
).setParseAction(
    lambda s, l, t: Atom(t[1], constructors[t[0]])
)

function = (
    pp.MatchFirst([pp.Keyword(t) for t in functions.keys()])
).setParseAction(
    lambda s, l, t: Atom(t[0], functions[t[0]])
)

expr = pp.infixNotation(
    constructor | function,
    [(
        None, 2, pp.opAssoc.LEFT,
        lambda s, l, t: reduce(App, t[0])
    )])

print(expr.parseString("ratio (ratioV a) (ratioV b)")[0])
