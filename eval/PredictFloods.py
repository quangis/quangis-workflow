from transformation_algebra import Query
from ..cct import CCT, AND, R3a, R2, R3, Obj, Reg, Nom, Ratio, Ord, Loc, Itv  # type: ignore

# flood prediction

# input: dem: R2(L, Itv)
# input: pour point: R3a(Obj, Reg, Nom)

eval_flood = Query(CCT, [R2(Ord, Ratio), R2(Ord, Reg), R2(Loc, Ratio), AND(
    [R3(Loc, Ratio, Loc), R2(Loc, Itv)],
    [R2(Reg, Nom), R3a(Obj, Reg, Nom)]
)])
