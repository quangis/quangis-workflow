# This script will preprocess task graphs so that types of the form `R(Obj)` 
# are transforrmd into `R(Val)` and `R(Obj, Reg * Nom)` are transformed into 
# `R(Val, Val * Val)`. In other words,

from rdflib import Graph, Literal
from sys import argv
from quangis.namespace import CCT_
from quangis.cctrans import cct, Val
from transforge.type import TypeOperation, TypeInstance


def rewrite(t: TypeInstance) -> TypeOperation:
    if isinstance(t, TypeOperation):
        if len(t.params) == 0:
            return Val
        else:
            return t.operator(*(rewrite(p) for p in t.params))
    else:
        raise RuntimeError


def process(path: str) -> Graph:
    g = Graph()
    g.parse(path)
    for node, ltype in g.subject_objects(CCT_.type):
        assert isinstance(ltype, Literal)
        old_type = ltype.value
        new_type = str(rewrite(cct.parse_type(old_type)))
        g.remove((node, CCT_.type, ltype))
        g.add((node, CCT_.type, Literal(new_type)))
    return g


if __name__ == "__main__":
    g = process(argv[1])
    print(g.serialize())
