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
Entity = partial(TypeOperator)
V = Entity("entity")
O = Entity("object")  # type: ignore
S = Entity("region")
L = Entity("location")
Q = Entity("quality")
Nom = Entity("nominal")
Bool = Entity("boolean")
Ord = Entity("ordinal")
Count = Entity("count")
Ratio = Entity("ratio")
Itv = Entity("interval")

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
    "avg": R(x, Itv) ** Itv | {x: Subtype(V)},
    "min": R(x, Ord) ** Ord | {x: Subtype(V)},
    "max": R(x, Ord) ** Ord | {x: Subtype(V)},

    # conversions
    "reify": R(L) ** S,
    "deify": S ** R(L),
    "get": R(x) ** x | {x: Subtype(V)},
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
    "pi1": x ** y | {y: Contains(x, at=1)},
    "pi2": x ** y | {y: Contains(x, at=2)},
    "pi3": x ** y | {y: Contains(x, at=3)},
    "sigmae": x ** y ** x | {x: Subtype(Q), y: Contains(x)},
    "sigmale": x ** y ** x | {x: Subtype(Ord), y: Contains(x)},
    "bowtie": x ** R(y) ** x | {y: Subtype(V), x: Contains(y)},
    "bowtie*":
        R(x, y, x) ** R(x, y) ** R(x, y, x) | {y: Subtype(Q), x: Subtype(V)},
    "bowtie_": (Q ** Q ** Q) ** R(V, Q) ** R(V, Q) ** R(V, Q),
    "groupbyL":
        (R(y, Q) ** Q) ** R(x, Q, y) ** R(x, Q) | {x: Subtype(V), y: Subtype(V)},
    "groupbyR":
        (R(x, Q) ** Q) ** R(x, Q, y) ** R(y, Q) | {x: Subtype(V), y: Subtype(V)},
}

algebra = Algebra(constructors, functions)
