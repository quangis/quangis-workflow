from __future__ import annotations

from functools import reduce
import pyparsing as pp


class Expr(object):
    pass


class App(Expr):
    def __init__(self, f, x):
        self.f = f
        self.x = x

    def __str__(self):
        return "({} {})".format(self.f, self.x)


expr = pp.infixNotation(
    pp.Word(pp.alphanums + '*_'),
    [(
        None,
        2,
        pp.opAssoc.LEFT,
        lambda s, l, t: reduce(App, t[0])
    )])

print(expr.parseString("""groupby_avg bowtie* sigmae lotopo deify merge pi2
    sigmae objectregions muni object Utrecht bowtie objectregions neighborhoods
    pi1 sigmae otopo objectregions neighborhoods (sigmae (objectregions muni)
    (object Utrecht)) in in interpol pointmeasures temperature deify merge pi2
    sigmae objectregions muni object Utrecht""")[0])
