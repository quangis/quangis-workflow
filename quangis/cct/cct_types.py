from __future__ import annotations

from typing import Optional, TypeVar
import typing as t


class Type(object):
    def __rshift__(a: Type, b: Type) -> Op:  # ** would be rtl assoc
        return Op(a, b)

    @staticmethod
    def unify(a: Type, b: Type) -> Optional[Type]:
        if type(a) != type(b):
            return None
        elif isinstance(a, Val) and isinstance(b, Val):
            if a.subsumes(b):
                return a
        return None


class Op(Type):
    def __init__(self, inp: Type, out: Type):
        self.inp = inp
        self.out = out

    def __str__(self):
        return "({} >> {})".format(self.inp, self.out)


class Val(Type):
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


class Union(Type):
    def __init__(self, *types):
        self._types = types

    def __str__(self):
        return " & ".join(map(str, self._types))


class Rel(Type):
    pass


class R1(Rel):
    def __init__(self, a: t.Union[Val, Var]):
        self.a = a

    def __str__(self):
        return "ρ({})".format(self.a)


class R2(Rel):
    def __init__(self, a: t.Union[Val, Var], b: t.Union[Val, Var]):
        self.a = a
        self.b = b

    def __str__(self):
        return "ρ({}, {})".format(self.a, self.b)


class R3(Rel):
    def __init__(self, a: t.Union[Val, Var], b: t.Union[Val, Var], c: t.Union[Val, Var]):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return "ρ({}, {}, {})".format(self.a, self.b, self.b)


T = TypeVar('T', Val, Rel)


class Var(Type):
    def __init__(self, i: int, t: t.Type[t.Union[Val, Rel]] = Val):
        self.id = i
        self.type = t

    def __str__(self):
        if self.type == Val:
            return "t{}".format(self.id)
        elif self.type == Rel:
            return "R{}".format(self.id)
        else:
            return "???"


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


base_types = {
    "ratio":
        Ratio >> (Ratio >> Ratio),
    "count":
        R1(O) >> Ratio,
    "groupbyL":
        (R2(Var(1), Q) >> Q) >>
        (R3(Var(1), Q, Var(2)) >> R2(Var(2), Q)),
    "join":
        Var(1, Rel) >> (R1(Var(2)) >> Var(1, Rel)),
    "invert": Union(
        R2(L, Ord) >> R2(Ord, S),
        R2(L, Nom) >> R2(S, Nom)
        )
}


if __name__ == '__main__':
    for k, v in base_types.items():
        print(k, ':',  v)

