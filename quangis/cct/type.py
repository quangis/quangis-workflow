"""
Be warned: This module heavily abuses overloading of Python's standard
operators. It also deviates from Python's convention of using capitalized names
for classes and lowercase for values. These decisions were made to get an
interface that is as close as possible to its formal type system counterpart.
"""
from __future__ import annotations

from typing import Optional, TypeVar, List, Union, Type, Dict, Tuple


class AlgType(object):
    """
    The class "AlgType" is the superclass for value types and relationship
    types in the transformation algebra.
    """

    def __init__(self):
        raise RuntimeError("Do not instantiate on its own")

    def __rshift__(a: AlgType, b: AlgType) -> Transformation:
        """
        This is an overloaded (ab)use of Python's right-shift operator. It
        allows us to use the infix operator >> for the arrow in function
        signatures.

        Note that this operator is left-to-right associative, which is
        non-standard behaviour for function application. __pow__ (for the **
        operator) would be right-to-left associative, but is less intuitive to
        read.
        """
        return Transformation(a, b)

    def __or__(a: AlgType, b: Dict[TypeVariable, TypeClass]) -> AlgType:
        """
        """
        #for constraint in b:
        #    return a.constrain(b)
        return a

    #def constrain(self, constraint: TypeConstraint):
    #    self.

    def substitute(self, substitution) -> AlgType:
        return self


class TypeOperator(AlgType):
    """
    n-ary type constructor.
    """

    def __init__(self, name: str, *types: AlgType):
        self.name = name
        self.types = list(types)

    def __str__(self) -> str:
        return "( {} {})".format(self.name, " ".join(map(str, self.types)))

    def __repr__(self):
        return self.__str__()

    @property
    def arity(self) -> int:
        return len(self.types)


class Transformation(TypeOperator):
    def __init__(self, input_type: AlgType, output_type: AlgType):
        super().__init__("op", input_type, output_type)


class RelationType(TypeOperator):
    def __init__(self, *types: Union[EntityType, TypeVariable]):
        super().__init__("rel", *types)

    def subsumes(self, other: RelationType) -> bool:
        return self.arity == other.arity and \
            all(s.subsumes(t) for s, t in zip(self.types, other.types))


class EntityType(TypeOperator):
    """
    A type for entity values. Note that entity types are implicitly
    polymorphic: subtypes are also acceptable.
    """

    def __init__(self, name: str, supertype: Optional[EntityType] = None):
        self.supertype = supertype
        super().__init__(name)

    def subsumes(self, other: Optional[EntityType]) -> bool:
        if other is None:
            return False
        else:
            return self.name == other.name or \
                self.subsumes(other.supertype)


class TypeVariable(AlgType):
    def __init__(self, i: int):
        self.id = i

    def __str__(self) -> str:
        return "t"+str(self.id)

    def __repr__(self):
        return self.__str__()

class TypeConstraint(object):
    def __init__(self, var: TypeVariable, typeclass: TypeClass):
        self.var = var.id
        self.typeclass = typeclass


class TypeClass(object):
    pass


# Value types
E = EntityType
V = E("entity")
O = E("object", V)  # type: ignore
S = E("region", V)
L = E("location", V)
Q = E("quality", V)
Nom = E("nominal", Q)
Bool = E("boolean", Nom)
Ord = E("ordinal", Nom)
Count = E("count", Ord)
Ratio = E("ratio", Count)
Itv = E("interval", Ratio)

# Type synonyms for relation types
R = RelationType
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
x, y, z = map(TypeVariable, range(1, 4))


class Contains(TypeClass):
    """
    Typeclass for relation types that contain the given value type in one of
    their columns.
    """

    def __init__(self, domain: AlgType):
        self.domain = domain


class Sub(TypeClass):
    """
    Typeclass for value types that are subsumed by the given superclass.
    """

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


functions = {
    "ratio":
        Ratio >> (Ratio >> Ratio),
    "avg":
        R(x, Itv) >> Itv | {x: Sub(V)},
    "count":
        R(O) >> Ratio,
    "sigma_eq":
        x >> (y >> x) | {x: Sub(V), y: Contains(x)},
    "groupby_L":
        (R(x) >> Q) >> (R(x, Q, y) >> R(y)) | {x: Sub(), y: Sub()},
    "join":
        x >> (R(y) >> x) | {y: Sub(V), x: Contains(y)},
    "invert":
 #       Overloaded(
        R(L, Ord) >> R(Ord, S)
 #           R(L, Nom) >> R(S, Nom)
 #       )
}


Substitution = Dict[TypeVariable, AlgType]


def unify(subst: Substitution, a: AlgType, b: AlgType) -> Substitution:
    if isinstance(a, TypeOperator) and isinstance(b, TypeOperator):
        if a.name != b.name or a.arity != b.arity:
            raise RuntimeError("type mismatch")
        else:
            for s, t in zip(a.types, b.types):
                unify(subst, s, t)
    elif isinstance(a, TypeVariable):
        subst[a] = b
    elif isinstance(b, TypeVariable):
        subst[b] = a
    return subst


#def apply(f: AlgType, x: AlgType) -> Tuple[AlgType, Substitution]:
#    if isinstance(f, Transformation):
#        inference = unify(f.input_type, x)
#        f.output_type.substitute(inference)
#    else:
#        raise RuntimeError("typecheck")



if __name__ == '__main__':

    print(unify({}, R(x), R(y)))

    for k, v in functions.items():
        print(k, ':',  v)

