# Road-Access
# 7. What is the percentage of rural population within 2km distance to
# all-season roads in Shikoku, Japan?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND, IMMEDIATELY
from cct import cct, R3a, R1, R2, Obj, Reg, Nom, Ord, Count, Ratio, Loc, Bool, ratio, extrapol  # type: ignore

workflows = {REPO.InfrastructureAccess}

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

eval_infrastructure_eric = Query(cct, [R1(Ratio), AND(

    # rural_pop2
    [R3a(Obj, Ratio, Reg), R2(Obj, Reg), AND(

        # chochomoku
        R3a(Obj, Ratio, Reg),

        # rural
        [R2(Obj, Reg), R3a(Obj, Ord, Reg)]
    )],

    # rural_access1
    [R2(Reg, Ratio), AND(

        # rural_clip
        [R2(Reg, Ratio), R2(Obj, Reg), R3a(Obj, Ord, Reg)],

        # roads_buffer
        [R1(Reg), R2(Obj, Reg)]
    )]
)])

# ------------------------------------
# simon:

# count amount ratio
eval_infrastructure_simon = Query(cct, [R2(Reg, Ratio), AND(

    # rural clip and summing contentamount (rural_pop1)
    IMMEDIATELY(R2(Reg, Count), R3a(Obj, Reg, Count), AND(

        # chochomoku
        [R3a(Obj, Reg, Count)],

        # rural
        [R2(Obj, Reg), R3a(Obj, Reg, Nom)]
    )),

    # rural_access1 via areal interpolation
    [R2(Reg, Count), AND(

        # rural_clip
        [R3a(Obj, Reg, Count), AND(

            # chochomoku
            [R3a(Obj, Reg, Count)],

            # rural
            [R2(Obj, Reg), R3a(Obj, Reg, Nom)]
        )],

        # roads_buffer
        [R2(Loc, Bool), R3a(Obj, Reg, Nom)]
    )]
)])
