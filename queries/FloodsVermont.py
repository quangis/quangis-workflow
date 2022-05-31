# Floods
# 9. What is the stream runoff during a predicted rainstorm in Vermont, US?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import cct, ObjectInfo, R2, R3, Obj, Reg, Nom, Ratio, Ord, Loc, Itv, groupbyLR, size, max, accumulate, flowdirgraph, lgDist  # type: ignore

workflows = {REPO.FloodsVermont}

query = Query(cct,
    [R2(Ord, Ratio), groupbyLR, AND(
        size,
        [R2(Loc, Ord), groupbyLR, AND(
            max,
            [accumulate, flowdirgraph, R2(Loc, Itv)],
            lgDist
        )]
    )]
)


# Evaluation #################################################################

# flood prediction

# input: dem: R2(L, Itv)
# input: pour point: R3a(Obj, Reg, Nom)

old_eval_flood = Query(cct, [R2(Ord, Ratio), R2(Ord, Reg), R2(Loc, Ratio), AND(
    [R3(Loc, Ratio, Loc), R2(Loc, Itv)],
    [R2(Reg, Nom), ObjectInfo(Nom)]
)])

# corrected version (04/02/2022)
eval_flood = Query(cct, [R2(Ord, Ratio), R2(Loc, Ratio), AND(
    [R3(Loc, Ratio, Loc), R2(Loc, Itv)],
    [R2(Nom, Reg), ObjectInfo(Nom)]
)])