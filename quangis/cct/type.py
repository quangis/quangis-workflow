"""
Generic type system. Inspired loosely by Hindley-Milner type inference in
functional programming languages.

Be warned: This module abuses overloading of Python's standard operators. It
also deviates from Python's convention of using capitalized names for classes
and lowercase for values. These decisions were made to get an interface that is
as close as possible to its formal type system counterpart.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional


class AlgebraType(ABC):
    """
    Abstract base class for type operators and type variables. Note that basic
    types are just 0-ary type operators.
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

    @abstractmethod
    def __contains__(self, value: AlgebraType) -> bool:
        return NotImplemented

    @abstractmethod
    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> AlgebraType:
        return NotImplemented

    @abstractmethod
    def map(self, fn: Callable[[AlgebraType], AlgebraType]) -> AlgebraType:
        return NotImplemented

    def fresh(self) -> AlgebraType:
        """
        Create a fresh copy of this type, with unique new variables.
        """

        return self._fresh({})
        #ctx: Dict[TypeVar, TypeVar] = {}
#
#        def f(t):
#            if isinstance(t, TypeVar):
#                if self in ctx:
#                    return ctx[self]
#                else:
#                    new = TypeVar.new()
#                    ctx[self] = new
#                    return new
#            return t

#        return self.map(f)

    def apply(self, arg: AlgebraType) -> AlgebraType:
        raise RuntimeError("Cannot apply an argument to non-function type")

    def substitute(self, subst: Dict[TypeVar, AlgebraType]) -> AlgebraType:
        if isinstance(self, TypeOperator):
            self.types = [t.substitute(subst) for t in self.types]
        elif isinstance(self, TypeVar):
            if self in subst:
                return subst[self]
        else:
            raise RuntimeError("non-exhaustive pattern")
        return self

    def unify(a: AlgebraType, b: AlgebraType, ctx: Substitution) -> Substitution:
        if isinstance(a, TypeOperator) and isinstance(b, TypeOperator):
            if a.name != b.name or a.arity != b.arity:
                raise RuntimeError("type mismatch")
            else:
                for s, t in zip(a.types, b.types):
                    s.unify(t, ctx)
        elif isinstance(a, TypeVar):
            if a != b and a in b:
                raise RuntimeError("recursive type")
            else:
                ctx[a] = b
        elif isinstance(b, TypeVar):
            b.unify(a, ctx)
        return ctx


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
        if self.types:
            return "{}({})".format(self.name, ", ".join(map(str, self.types)))
        else:
            return self.name

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> TypeOperator:
        return TypeOperator(self.name, *(t._fresh(ctx) for t in self.types))

    def map(self, fn: Callable[[AlgebraType], AlgebraType]) -> AlgebraType:
        return TypeOperator(self.name, *map(fn, self.types))

    @property
    def arity(self) -> int:
        return len(self.types)


class Transformation(TypeOperator):
    def __init__(self, input_type: AlgebraType, output_type: AlgebraType):
        super().__init__("op", input_type, output_type)

    def map(self, fn: Callable[[AlgebraType], AlgebraType]) -> AlgebraType:
        return Transformation(*map(fn, self.types))

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> Transformation:
        return Transformation(*(t._fresh(ctx) for t in self.types))

    def __str__(self) -> str:
        return "({0} -> {1})".format(*self.types)

    def apply(self, arg: AlgebraType) -> AlgebraType:
        """
        Apply an argument to a function type to get its output type.
        """
        input_type, output_type = self.types
        env = input_type.unify(arg, {})
        return output_type.substitute(env)


class TypeVar(AlgebraType):

    counter = 0

    def __init__(self, i: int):
        self.id = i

    def __str__(self) -> str:
        return "x" + str(self.id)

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other: object):
        if isinstance(other, TypeVar):
            return self.id == other.id
        else:
            return False

    def __contains__(self, value: AlgebraType) -> bool:
        return self == value

    @classmethod
    def new(cls) -> TypeVar:
        new = TypeVar(cls.counter)
        cls.counter += 1
        return new

    def map(self, fn: Callable[[AlgebraType], AlgebraType]) -> AlgebraType:
        return fn(self)

    def _fresh(self, ctx: Dict[TypeVar, TypeVar]) -> TypeVar:
        if self in ctx:
            return ctx[self]
        else:
            new = type(self).new()
            ctx[self] = new
            return new


Substitution = Dict[TypeVar, AlgebraType]


class TypeClass(object):
    pass


class Contains(TypeClass):
    """
    Typeclass for relation types that contain the given value type in one of
    their columns.
    """

    def __init__(self, domain: AlgebraType, at: Optional[int] = None):
        self.domain = domain


class Subtype(TypeClass):
    """
    Typeclass for value types that are subsumed by the given superclass.
    """

    def __init__(self, supertype: TypeOperator):
        pass

