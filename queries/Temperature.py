# Temperature / amountFieldUtrecht
# 3. What is the average temperature for each neighbourhood in Utrecht?

from transformation_algebra.query import Query, AND
from cct import CCT, R3a, R2, Obj, Reg, Nom, Loc, Itv, groupbyLR, avg  # type: ignore


query = Query(CCT,
    [R3a(Obj, Reg, Itv), groupbyLR, AND(
        avg,
        R2(Loc, Itv)
    )]
)


# Evaluation #################################################################

# average temperature in Utrecht

# input cbsneighbours: R3a(Obj, Reg, Nom)
# input weather stations: R2(Reg, Itv)

eval_temperature = Query(CCT,
    [R3a(Obj, Reg, Itv), R2(Obj, Itv), AND(
        [R2(Loc, Itv), R2(Reg, Itv)],
        [R2(Obj, Reg), R3a(Obj, Reg, Nom)]
    )]
)
