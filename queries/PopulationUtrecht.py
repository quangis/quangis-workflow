# Population
# 2. What is the number of inhabitants for each neighbourhood in Utrecht?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND, OR
from cct import cct, ObjectInfo, R2, Obj, Reg, Nom, Count, groupbyLR, sum, count  # type: ignore

workflows = {REPO.PopulationUtrecht}

query = Query(cct,
    [ObjectInfo(Count), groupbyLR, OR(
        AND(sum, R2(Reg, Count)),
        AND(count, R2(Obj, Reg))
    )]
)

# Evaluation #################################################################

# number of people in neighborhoods

# input cbsneighborhoods: R3a(Obj, Reg, Nom)
# input cbsvierkant: R2(Reg, Count)

eval_population = Query(cct, [ObjectInfo(Count), R2(Obj, Count), AND(
    [R2(Obj, Reg), ObjectInfo(Nom)],
    [R2(Reg, Count)]
)])
