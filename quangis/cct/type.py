from __future__ import annotations

from typing import Optional, TypeVar, List, Union, Type, Dict


class TypeConstraint(object):
    pass


class CCTType(object):
    """
    The class "Type" is the superclass for value types and relationship types.
    """

    def __init__(self):
        raise RuntimeError("Do not instantiate on its own")

    def __pow__(a: CCTType, b: CCTType) -> Op:
        """
        See __rshift__.
        """
        return a.__rshift__(b)

    def __rshift__(a: CCTType, b: CCTType) -> Op:
        """
        This is an overloaded (ab)use of Python's right-shift operator. It
        allows us to use the infix operator >> for the arrow in function
        signatures.

        Note that this operator is left-to-right associative, which is
        non-standard behaviour for function application. __pow__ (for the **
        operator) would be right-to-left associative, but is less intuitive to
        read. We provide both.
        """
        return Op(a, b)

    def __or__(a: CCTType, b: TypeConstraint) -> Type:
        return a.constrain(b)

    @staticmethod
    def unify(a: CCTType, b: CCTType) -> Optional[CCTType]:
        if type(a) != type(b):
            return None
        elif isinstance(a, Val) and isinstance(b, Val):
            if a.subsumes(b):
                return a
        return None


class Op(CCTType):
    """
    A function type.
    """

    def __init__(self, inp: CCTType, out: CCTType):
        self.inp = inp
        self.out = out

    def __str__(self):
        return "({} >> {})".format(self.inp, self.out)


class Val(CCTType):
    """
    A value type.
    """

    def __init__(self, keyword: str, parent: Optional[Val] = None):
        self.keyword = keyword
        self.parent = parent

    def __str__(self):
        return self.keyword

    def subsumes(self, other: Optional[Val]) -> bool:
        if other is None:
            return False
        else:
            return self.keyword == other.keyword or \
                self.subsumes(other.parent)


class R(CCTType):
    """
    A relation type.
    """

    def __init__(self, *types: Union[Var, Val]):
        self.types = types
        self.arity = len(types)

    def __str__(self):
        return "R({})".format(list(map(str, self.types)))


T = TypeVar('T', Val, R)


class Var(CCTType):
    """
    A type variable.
    """

    def __init__(self, i: int):
        self.id = i

    def __str__(self) -> str:
        return str(self.id)


class Overloaded(CCTType):
    def __init__(self, *types):
        self._types = types

    def __str__(self):
        return " & ".join(map(str, self._types))


# Value types
V = Val("V")
O = Val("O", V)  # type: ignore
S = Val("S", V)
L = Val("L", V)
Q = Val("Q", V)
Nom = Val("Nom", Q)
Bool = Val("Bool", Nom)
Ord = Val("Ord", Nom)
Count = Val("Count", Ord)
Ratio = Val("Ratio", Count)
Itv = Val("Itv", Ratio)

# Type synonyms for relation types
SpatialField = R(L, Q)
InvertedField = R(Q, S)
FieldSample = R(S, Q)
ObjectExtent = R(O, S)
ObjectQuality = R(O, Q)
NominalField = R(L, Nom)
BooleanField = R(L, Bool)
NominalInvertedField = R(Nom, S)
BooleanInvertedField = R(Bool, S)


constructors: Dict[str, CCTType] = {
    "pointmeasures": R(S, Itv),
    "amountpatches": R(S, Nom),
    "contour": R(Ord, S),
    "objects": R(O, Ratio),
    "objectregions": R(O, S),
    "object": O,
    "contourline": R(Itv, S),
    "objectcounts": R(O, Count),
    "field": R(L, Ratio),
    "in": Nom,
    "region": S,
    "count": Count,
    "ratioV": Ratio,
    "interval": Itv,
    "ordinal": Ord,
    "nominal": Nom
}

functions = {
    "ratio":
        Ratio ** Ratio ** Ratio,
    "avg":
        R(Var(1), Itv) ** Itv,  #  | 1 in Domains
    "count":
        R(O) ** Ratio,
    "groupby_L":
        (R(Var(1)) ** Q) ** R(Var(1), Q, Var(2)) ** R(Var(2)),
    "join":
        Var(1) ** R(Var(2)) ** Var(1),
    "invert": Overloaded(
        R(L, Ord) ** R(Ord, S),
        R(L, Nom) ** R(S, Nom)
        )
}


if __name__ == '__main__':
    for k, v in function_types.items():
        print(k, ':',  v)

