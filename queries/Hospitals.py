# Hospitals
# 4. What is the travel distance to the nearest hospital in California?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import cct, ObjectInfo, R2, R3, Obj, Reg, Nom, Ratio, Loc, groupbyLR, min, nDist  # type: ignore

workflows = {REPO.HospitalsNetwork, REPO.HospitalsNear}

query = Query(cct,
    [ObjectInfo(Ratio), groupbyLR, AND(
        min,
        nDist,
        R2(Obj, Reg)
    )]
)


# Evaluation #################################################################

# hospitalsNear

# input R3a(Obj, Nom, Reg)  # roads
# input R2(Obj, Loc)  # hospital points
# input R2(Obj, Loc)  # incident location

# eval_hospitalsnear_eric = Query(cct, [R2(Obj, Loc), AND(
#     R3a(Obj, Nom, Reg),
#     R2(Obj, Loc),
#     R2(Obj, Loc)
# )])

# --------------------------------------------
# hospitalsNetwork

# input R3a(Obj, Nom, Reg)  # roads
# input R2(Obj, Loc)  # hospital points
# input R2(Obj,  Loc)  # incident location

# eval_eric_hospitalsnetwork = Query(cct, [R2(Obj, Nom), R3a(Obj, Nom, Obj), AND(
#     R3a(Obj, Nom, Reg),
#     R2(Obj, Loc),
#     R2(Obj, Loc)
# )])

# ------------------
# simon:
old_eval_hospitalsnear_simon = Query(cct,
    [R2(Obj, Ratio), R3(Obj, Ratio, Obj), AND(
        # hospital points
        [ObjectInfo(Nom)],
        # incident location
        [ObjectInfo(Nom)]
    )]
)

old_eval_hospitalsnetwork_simon = Query(cct,
    [R2(Obj, Ratio), R3(Obj, Ratio, Obj), AND(
        # Roads
        [ObjectInfo(Nom)],
        # Hospital points
        [ObjectInfo(Nom)],
        # Incident location
        [ObjectInfo(Nom)]
    )]
)


# Corrected version: 2022/02/04
eval_hospitalsnear = Query(cct,
    [ObjectInfo(Ratio), R3(Obj, Ratio, Obj), AND(
        # hospital points
        [ObjectInfo(Nom)],
        # incident location
        [ObjectInfo(Nom)]
    )]
)

eval_hospitalsnetwork = Query(cct,
    [ObjectInfo(Ratio), R3(Obj, Ratio, Obj), AND(
        # Roads
        [ObjectInfo(Nom)],
        # Hospital points
        [ObjectInfo(Nom)],
        # Incident location
        [ObjectInfo(Nom)]
    )]
)
