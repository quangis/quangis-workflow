from transformation_algebra import Query
from ..cct import CCT, AND, R3a, R2, Obj, Reg, Nom, Count  # type: ignore

# number of people in neighborhoods

# input cbsneighborhoods: R3a(Obj, Reg, Nom)
# input cbsvierkant: R2(Reg, Count)

eval_population = Query(CCT, [R3a(Obj, Reg, Count), R2(Obj, Count), AND(
    [R2(Obj, Reg), R3a(Obj, Reg, Nom)],
    [R2(Reg, Count)]
)])
