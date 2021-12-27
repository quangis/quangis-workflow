from transformation_algebra.query import Query, AND
from cct import CCT, R3a, R2, Obj, Reg, Nom, Loc, Itv  # type: ignore

# average temperature in Utrecht

# input cbsneighbours: R3a(Obj, Reg, Nom)
# input weather stations: R2(Reg, Itv)

eval_temperature = Query(CCT, [R3a(Obj, Reg, Itv), R2(Obj, Itv), AND(
    [R2(Loc, Itv), R2(Reg, Itv)],
    [R2(Obj, Reg), R3a(Obj, Reg, Nom)]
)])
