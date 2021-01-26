"""
The core concept transformation algebra.
"""

from functools import partial
from typing import Dict

from quangis.transformation.parser import make_parser, Expr
from quangis.transformation.type import TypeOperator, TypeVar, AlgebraType, \
    Sub, Contains


class Algebra(object):
    def __init__(
            self,
            functions: Dict[str, AlgebraType]):
        self.parser = make_parser(functions)

    def parse(self, string: str) -> Expr:
        return self.parser.parseString(string)[0]


# Type variables for convenience
x, y, z = (TypeVar() for _ in range(0, 3))

# Entity value types
Entity = partial(TypeOperator)
V = Entity("entity")
O = Entity("object", supertype=V)  # type: ignore
S = Entity("region", supertype=V)
L = Entity("location", supertype=V)
Q = Entity("quality", supertype=V)
Nom = Entity("nominal", supertype=Q)
Bool = Entity("boolean", supertype=Nom)
Ord = Entity("ordinal", supertype=Nom)
Count = Entity("count", supertype=Ord)
Ratio = Entity("ratio", supertype=Count)
Itv = Entity("interval", supertype=Ratio)

# Relation types and type synonyms
R = partial(TypeOperator, "R")
SpatialField = R(L, Q)
InvertedField = R(Q, S)
FieldSample = R(S, Q)
ObjectExtent = R(O, S)
ObjectQuality = R(O, Q)
NominalField = R(L, Nom)
BooleanField = R(L, Bool)
NominalInvertedField = R(Nom, S)
BooleanInvertedField = R(Bool, S)

# Constructors are functions that introduce data of a certain type
functions = {

    # data constructors
    "pointmeasures": R(S, Itv),
    "amountpatches": R(S, Nom),
    "contour": R(Ord, S),
    "objects": R(O, Ratio),
    "objectregions": R(O, S),
    "contourline": R(Itv, S),
    "objectcounts": R(O, Count),
    "field": R(L, Ratio),
    "object": R(O),
    "region": R(S),
    "in": R(Nom),
    "countV": R(Count),
    "ratioV": R(Ratio),
    "interval": R(Itv),
    "ordinal": R(Ord),
    "nominal": R(Nom),

    # Functions are type transformations in the algebra, without any particular
    # implementation

    # functional
    "compose": (y ** z) ** (x ** y) ** (x ** z),

    # derivations
    "ratio": Ratio ** Ratio ** Ratio,

    # aggregations of collections
    "count": R(O) ** Ratio,
    "size": R(L) ** Ratio,
    "merge": R(S) ** S,
    "centroid": R(L) ** L,

    # statistical operations
    "avg": R(V, Itv) ** Itv,
    "min": R(V, Ord) ** Ord,
    "max": R(V, Ord) ** Ord,
    "sum": R(V, Count) ** Count,

    # conversions
    "reify": R(L) ** S,
    "deify": S ** R(L),
    "get": R(x) ** x | {x: Sub(V)},
    "invert": R(L, Ord) ** R(Ord, S),  # TODO overload R(L, Nom) ** R(S, Nom)
    "revert": R(Ord, S) ** R(L, Ord),  # TODO overload

    # quantified relations
    "oDist": R(O, S) ** R(O, S) ** R(O, Ratio, O),
    "lDist": R(L) ** R(L) ** R(L, Ratio, L),
    "loDist": R(L) ** R(O, S) ** R(L, Ratio, O),
    "oTopo": R(O, S) ** R(O, S) ** R(O, Nom, O),
    "loTopo": R(L) ** R(O, S) ** R(L, Nom, O),
    "nDist": R(O) ** R(O) ** R(O, Ratio, O) ** R(O, Ratio, O),
    "lVis": R(L) ** R(L) ** R(L, Itv) ** R(L, Bool, L),
    "interpol": R(S, Itv) ** R(L) ** R(L, Itv),

    # amount operations
    "fcont": R(L, Itv) ** Ratio,
    "ocont": R(O, Ratio) ** Ratio,

    # relational
    "pi1":
        x ** y | {y: Contains(x, at=1)},
    "pi2":
        x ** y | {y: Contains(x, at=2)},
    "pi3":
        x ** y | {y: Contains(x, at=3)},
    "sigmae":
        x ** y ** x | {x: Sub(Q), y: Contains(x)},
    "sigmale":
        x ** y ** x | {x: Sub(Ord), y: Contains(x)},
    "bowtie":
        x ** R(y) ** x | {y: Sub(V), x: Contains(y)},
    "bowtie*":
        R(x, y, x) ** R(x, y) ** R(x, y, x) | {y: Sub(Q), x: Sub(V)},
    "bowtie_":
        (Q ** Q ** Q) ** R(V, Q) ** R(V, Q) ** R(V, Q),
    "groupbyL":
        (R(y, Q) ** Q) ** R(x, Q, y) ** R(x, Q) | {x: Sub(V), y: Sub(V)},
    "groupbyR":
        (R(x, Q) ** Q) ** R(x, Q, y) ** R(y, Q) | {x: Sub(V), y: Sub(V)},
}

algebra = Algebra(functions)
