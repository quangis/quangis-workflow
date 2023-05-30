# This script will preprocess task graphs so that types of the form `R(Obj)` 
# are converted into `R(Val)` and `R(Obj, Reg * Nom)` are converted into 
# `R(Val, Val * Val)`, or whatever canonical type (excluding `Top`, except 
# where the type already contained `Top`) is highest.

from rdflib import Graph, Literal
from sys import argv
from quangis.namespace import CCT
from quangis.cctrans import cct, Val
from transforge.type import TypeOperation, TypeInstance, Top

def top_eq(left: TypeInstance, right: TypeInstance) -> bool:
    """Return true only if every Top type that occurs in the right type also 
    occurs in the left type at the same place."""
    if len(right.params) == 0:
        return right.operator != Top or left.operator == Top
    else:
        assert left.operator == right.operator
        assert len(left.params) == len(right.params), f"{left} {right}"
        return all(top_eq(l, r) for l, r in zip(left.params, right.params))


def rewrite(t: TypeInstance) -> TypeOperation:
    if isinstance(t, TypeOperation):
        while True:
            st = set(t1 for t1 in cct.supertypes(t) if top_eq(t, t1))
            if len(st) == 0:
                return t
            else:
                t = st.pop()
    else:
        raise RuntimeError


def process(path: str) -> Graph:
    g = Graph()
    g.parse(path)
    for node, ltype in g.subject_objects(CCT.type):
        assert isinstance(ltype, Literal)
        old_type = ltype.value
        new_type = str(rewrite(cct.parse_type(old_type)))
        g.remove((node, CCT.type, ltype))
        g.add((node, CCT.type, Literal(new_type)))
    return g


if __name__ == "__main__":
    g = process(argv[1])
    print(g.serialize())
