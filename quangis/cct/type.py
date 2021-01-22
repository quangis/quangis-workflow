"""
Be warned: This module heavily abuses overloading of Python's standard
operators.
"""

from __future__ import annotations

from typing import Optional, TypeVar, List, Union, Type, Dict


class TypeConstraint(object):
    def __init__(self, var: Var, typeclass: TypeClass):
        self.var = var.id
        self.typeclass = typeclass


class AlgType(object):
    """
    The class "AlgType" is the superclass for value types and relationship
    types in the transformation algebra.
    """

    def __init__(self):
        raise RuntimeError("Do not instantiate on its own")

    def __pow__(a: AlgType, b: AlgType) -> Transformation:
        """
        See __rshift__.
        """
        return a.__rshift__(b)

    def __rshift__(a: AlgType, b: AlgType) -> Transformation:
        """
        This is an overloaded (ab)use of Python's right-shift operator. It
        allows us to use the infix operator >> for the arrow in function
        signatures.

        Note that this operator is left-to-right associative, which is
        non-standard behaviour for function application. __pow__ (for the **
        operator) would be right-to-left associative, but is less intuitive to
        read. We provide both.
        """
        return Transformation(a, b)

    def __or__(a: AlgType, b: Dict[Var, TypeClass]) -> AlgType:
        """
        """
        for constraint in b:
            return a.constrain(b)
        return a

    #def constrain(self, constraint: TypeConstraint):
    #    self.

    @staticmethod
    def unify(a: AlgType, b: AlgType) -> Optional[AlgType]:
        if type(a) != type(b):
            return None
        elif isinstance(a, Val) and isinstance(b, Val):
            if a.subsumes(b):
                return a
        return None


class Transformation(AlgType):
    """
    A function type.
    """

    def __init__(self, inp: AlgType, out: AlgType):
        self.inp = inp
        self.out = out

    def __str__(self):
        return "({} >> {})".format(self.inp, self.out)


class Val(AlgType):
    """
    A type for values.
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


class R(AlgType):
    """
    A relation type.
    """

    def __init__(self, *types: Union[Var, Val, str]):
        self.types = types
        self.arity = len(types)

    def __str__(self):
        return "R({})".format(list(map(str, self.types)))


T = TypeVar('T', Val, R)


class Var(AlgType):
    """
    A type variable.
    """

    def __init__(self, i: str):
        self.id = i

    def __str__(self) -> str:
        return self.id

    def of(self, b: TypeClass) -> TypeConstraint:
        return TypeConstraint(self, b)


class TypeClass(object):
    pass



class Overloaded(AlgType):
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

# Convenience variables
x, y, z = Var("x"), Var("y"), Var("z")


class HasColumn(TypeClass):
    def __init__(self, domain: AlgType):
        self.domain = domain


class Value(TypeClass):
    def __init__(self, *superclasses):
        pass


constructors: Dict[str, AlgType] = {
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


def t(x):
    return Var(str(x))


functions = {
    "ratio":
        Ratio >> (Ratio >> Ratio),
    "avg":
        R(x, Itv) >> Itv | {x: Value()},
    "count":
        R(O) >> Ratio,
    "sigma_eq":
        x >> (y >> x) | {x: Value(Q), y: HasColumn(x)},
    "groupby_L":
        (R(x) >> Q) >> (R(x, Q, y) >> R(y)) | {x: Value(), y: Value()},
    "join":
        x >> (R(y) >> x) | {y: Value(), x: HasColumn(y)},
    "invert":
        Overloaded(
            R(L, Ord) >> R(Ord, S),
            R(L, Nom) >> R(S, Nom)
        )
}


if __name__ == '__main__':
    for k, v in functions.items():
        print(k, ':',  v)

