# Road-Access
# 7. What is the percentage of rural population within 2km distance to
# all-season roads in Shikoku, Japan?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND, STEPS
from cct import cct, ObjectInfo, R1, R2, Obj, Reg, Nom, Ord, Count, Ratio, Loc, Bool, ratio, extrapol  # type: ignore

workflows = {REPO.InfrastructureAccessShinkoku}

query = Query(cct,
    [R2(Reg, Ratio), AND(
        ratio,
        [R2(Reg, Ratio), AND(
            [extrapol, R2(Obj, Reg)],
            R2(Reg, Count)
        )]
    )]
)


# Evaluation #################################################################

# R3a(Obj, Ord, Reg)  # urbanization
# R3a(Obj, Ratio, Reg)  # chochomoku
# R2(Obj, Reg)  # roads

# eval_eric_infrastructure = Query(cct, [R1(Ratio), AND(

#     # rural_pop2
#     [ObjectInfo(Reg), R2(Obj, Reg), AND(

#         # chochomoku
#         ObjectInfo(Reg),

#         # rural
#         [R2(Obj, Reg), ObjectInfo(Reg)]
#     )],

#     # rural_access1
#     [R2(Reg, Ratio), AND(

#         # rural_clip
#         [R2(Reg, Ratio), R2(Obj, Reg), ObjectInfo(Reg)],

#         # roads_buffer
#         [R1(Reg), R2(Obj, Reg)]
#     )]
# )])

# ------------------------------------
# simon:

# count amount ratio
eval_infrastructure = Query(cct, [R2(Reg, Ratio), AND(

    # rural clip and summing contentamount (rural_pop1)
    [R2(Reg, Count), ObjectInfo(Count), AND(

        # chochomoku
        [ObjectInfo(Count)],

        # rural
        [R2(Obj, Reg), ObjectInfo(Nom)]
    )],

    # rural_access1 via areal interpolation
    [R2(Reg, Count), AND(

        # rural_clip
        [ObjectInfo(Count), AND(

            # chochomoku
            [ObjectInfo(Count)],

            # rural
            [R2(Obj, Reg), ObjectInfo(Nom)]
        )],

        # roads_buffer
        [R2(Loc, Bool), ObjectInfo(Nom)]
    )]
)])
