"""
The core concept transformation algebra.
"""

from functools import partial
from typing import Optional, List, Union, Type, Dict, Tuple

from quangis.cct.parser import make_parser, Expr
from quangis.cct.type import TypeOperator, TypeVar, AlgebraType, \
    Subtype, Contains


class Algebra(object):
    def __init__(
            self,
            functions: Dict[str, AlgebraType],
            constructors: Dict[str, AlgebraType]):
        self.parser = make_parser(functions, constructors)

    def parse(self, string: str) -> Expr:
        return self.parser.parseString(string)[0]


# Type variables for convenience
x, y, z = (TypeVar.new() for _ in range(0, 3))

# Entity value types
E = partial(TypeOperator)
V = E("entity")
O = E("object")  # type: ignore
S = E("region")
L = E("location")
Q = E("quality")
Nom = E("nominal")
Bool = E("boolean")
Ord = E("ordinal")
Count = E("count")
Ratio = E("ratio")
Itv = E("interval")

# Relation types and type synonyms
R = partial(TypeOperator, "rel")
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
constructors: Dict[str, AlgebraType] = {
    "pointmeasures": R(S, Itv),
    "amountpatches": R(S, Nom),
    "contour": R(Ord, S),
    "objects": R(O, Ratio),
    "objectregions": R(O, S),
    "contourline": R(Itv, S),
    "objectcounts": R(O, Count),
    "field": R(L, Ratio),
    "object": O,
    "region": S,
    "in": Nom,
    "count": Count,
    "ratioV": Ratio,
    "interval": Itv,
    "ordinal": Ord,
    "nominal": Nom
}

# Functions are type transformations in the algebra, without any particular
# implementation
functions = {
    "compose":
        (y ** z) ** (x ** y) ** (x ** z),
    "ratio":
        Ratio ** Ratio ** Ratio,
    "avg":
        R(x, Itv) ** Itv | {x: Subtype(V)},
    "count":
        R(O) ** Ratio,
    "sigma_eq":
        x ** y ** x | {x: Subtype(Q), y: Contains(x)},
    "groupby_L":
        (R(x) ** Q) ** R(x, Q, y) ** R(y) | {x: Subtype(V), y: Subtype(V)},
    "join":
        x ** R(y) ** x | {y: Subtype(V), x: Contains(y)},
    "invert":
        R(L, Ord) ** R(Ord, S)  # R(L, Nom) ** R(S, Nom)
}

algebra = Algebra(constructors, functions)
print(algebra.parse("ratio (ratioV a) (ratioV b)"))
