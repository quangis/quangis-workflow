"""
Generic type system. Inspired loosely by Hindley-Milner type inference in
programming languages.

Be warned: This module abuses overloading of Python's standard operators. It
also deviates from Python's convention of using capitalized names for classes
and lowercase for values. These decisions were made to get an interface that is
as close as possible to its formal type system counterpart.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List, Union, Type, Dict, Tuple


class AlgebraType(ABC):
    """
    The class "AlgebraType" is the superclass for value types and relationship
    types in the transformation algebra.
    """

    def __pow__(self: AlgebraType, other: AlgebraType) -> Transformation:
        """
        This is an overloaded (ab)use of Python's exponentiation operator. It
        allows us to use the infix operator ** for the arrow in function
        signatures.

        Note that this operator is one of the few that is right-to-left
        associative, matching the conventional behaviour of the function arrow.
        The right-bitshift operator >> (for __rshift__) would have been more
        intuitive visually, but does not have this property.
        """
        return Transformation(self, other)

    def __or__(a: AlgebraType, b: Dict[TypeVar, TypeClass]) -> AlgebraType:
        """
        """
        #for constraint in b:
        #    return a.constrain(b)
        return a

    #def constrain(self, constraint: TypeConstraint):
    #    self.

    def __repr__(self):
        return self.__str__()

    def substitute(self, subst: Dict[TypeVar, AlgebraType]) -> AlgebraType:
        if isinstance(self, TypeOperator):
            self.types = [t.substitute(subst) for t in self.types]
        elif isinstance(self, TypeVar):
            if self in subst:
                return subst[self]
        return self

    @abstractmethod
    def __contains__(self, value: AlgebraType) -> bool:
        return NotImplemented

    @abstractmethod
    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> AlgebraType:
        return NotImplemented

    def fresh(self) -> AlgebraType:
        """
        Create a fresh copy of this type, with unique new variables.
        """

        return self._fresh({})

    def apply(self, arg: AlgebraType) -> AlgebraType:
        raise RuntimeError("Cannot apply an argument to non-function type")


class TypeOperator(AlgebraType):
    """
    n-ary type constructor.
    """

    def __init__(self, name: str, *types: AlgebraType):
        self.name = name
        self.types = list(types)

    def __eq__(self, other: object):
        if isinstance(other, TypeOperator):
            return self.name == other.name and \
               self.arity == other.arity and \
               all(self.types[i] == other.types[i]
                   for i in range(0, self.arity))
        else:
            return False

    def __contains__(self, value: AlgebraType) -> bool:
        return value == self or any(value in t for t in self.types)

    def __str__(self) -> str:
        return "{}({})".format(self.name, ", ".join(map(str, self.types)))

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> TypeOperator:
        return TypeOperator(self.name, *(t._fresh(ctx) for t in self.types))

    @property
    def arity(self) -> int:
        return len(self.types)


class Transformation(TypeOperator):
    def __init__(self, input_type: AlgebraType, output_type: AlgebraType):
        super().__init__("op", input_type, output_type)

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> Transformation:
        return Transformation(*(t._fresh(ctx) for t in self.types))

    def apply(self, arg: AlgebraType) -> AlgebraType:
        """
        Apply an argument to a function type to get its output type.
        """
        input_type, output_type = self.types
        env = unify(input_type, arg, {})
        return output_type.substitute(env)


class RelationType(TypeOperator):
    def __init__(self, *types: AlgebraType):
        super().__init__("rel", *types)

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> RelationType:
        return RelationType(*(t._fresh(ctx) for t in self.types))

    def is_subtype(self, other: RelationType) -> bool:
        return self.arity == other.arity and \
            all(s.is_subtype(t) for s, t in zip(self.types, other.types))


class EntityType(TypeOperator):
    """
    A type for basic entity values. Note that entity types are implicitly
    polymorphic: subtypes are also acceptable.
    """

    def __init__(self, name: str, supertype: Optional[EntityType] = None):
        self.supertype = supertype
        super().__init__(name)

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> EntityType:
        return EntityType(self.name, self.supertype)

    def is_subtype(self, other: Optional[EntityType]) -> bool:
        if other is None:
            return False
        else:
            return self.name == other.name or \
                self.is_subtype(other.supertype)


class TypeVar(AlgebraType):

    counter = 0

    def __init__(self, i: int):
        self.id = i

    def __str__(self) -> str:
        return "Var"+str(self.id)

    def __contains__(self, value: AlgebraType) -> bool:
        return self == value

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> TypeVar:
        if self in ctx:
            return ctx[self]
        else:
            cls = type(self)
            new = TypeVar(cls.counter)
            cls.counter += 1
            ctx[self] = new
            return new

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
x, y, z = map(TypeVar, range(1, 4))


class TypeClass(object):
    pass


class Contains(TypeClass):
    """
    Typeclass for relation types that contain the given value type in one of
    their columns.
    """

    def __init__(self, domain: AlgebraType):
        self.domain = domain


class Subtype(TypeClass):
    """
    Typeclass for value types that are subsumed by the given superclass.
    """

    def __init__(self, supertype: EntityType):
        pass


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
 #       Overloaded(
        R(L, Ord) ** R(Ord, S)
 #           R(L, Nom) ** R(S, Nom)
 #       )
}


Substitution = Dict[TypeVar, AlgebraType]


def unify(a: AlgebraType, b: AlgebraType, ctx: Substitution) -> Substitution:
    if isinstance(a, TypeOperator) and isinstance(b, TypeOperator):
        if a.name != b.name or a.arity != b.arity:
            raise RuntimeError("type mismatch")
        else:
            for s, t in zip(a.types, b.types):
                unify(s, t, ctx)
    elif isinstance(a, TypeVar):
        if a != b and a in b:
            raise RuntimeError("recursive type")
        else:
            ctx[a] = b
    elif isinstance(b, TypeVar):
        unify(b, a, ctx)
    return ctx
