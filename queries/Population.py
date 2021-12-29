# Population
# 2. What is the number of inhabitants for each neighbourhood in Utrecht?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND, OR
from cct import CCT, R3a, R2, Obj, Reg, Nom, Count, groupbyLR, sum, count  # type: ignore

workflows = {REPO.AmountObjectsUtrecht}

query = Query(CCT,
    [R3a(Obj, Reg, Count), groupbyLR, OR(
        AND(sum, R2(Reg, Count)),
        AND(count, R2(Obj, Reg))
    )]
)

# Evaluation #################################################################

# number of people in neighborhoods

# input cbsneighborhoods: R3a(Obj, Reg, Nom)
# input cbsvierkant: R2(Reg, Count)

eval_population = Query(CCT, [R3a(Obj, Reg, Count), R2(Obj, Count), AND(
    [R2(Obj, Reg), R3a(Obj, Reg, Nom)],
    [R2(Reg, Count)]
)])
