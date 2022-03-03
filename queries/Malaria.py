# Malaria
# 10. What is the malaria incidence rate per 1000 inhabitants in the Democratic
# Republic of the Congo?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import cct, ObjectInfo, R2, Obj, Reg, Nom, Count, Ratio, ratio, sum, groupbyLR  # type: ignore

workflows = {REPO.Malaria}

malaria = Query(cct,
    [ObjectInfo(Ratio), AND(
        ratio,
        R2(Obj, Count),
        [R2(Obj, Count), groupbyLR, AND(
            sum,
            R2(Reg, Count)
        )]
    )]
)


# Evaluation #################################################################

# R3a(Obj, Nom, Reg)  # countries
# R3a(Obj, Nom, Reg)  # adminRegions
# R2(Reg, Ratio)  # population
# R2(Obj, Ratio)  # countryIncidence
# R2(Obj, Ratio)  # adminIncidence

# eric_eval_malaria = Query(cct, [R2(Obj, Ratio), AND(
#     # adminDRC3
#     AND(

#         # adminDRC2
#         R3a(Obj, Nom, Reg),

#         # popAdminDRC
#         [R3a(Obj, Ratio, Reg), AND(

#             # population
#             R2(Reg, Ratio),

#             # adminDRC2
#             R3a(Obj, Nom, Reg)
#         )]
#     ),

#     # adminIncidence2
#     R2(Obj, Ratio)
# )])

# simon

eval_malaria = Query(cct, [ObjectInfo(Ratio), AND(

    # popAdminDRC
    [ObjectInfo(Count), AND(

        # population on cells
        R2(Reg, Count),

        # adminDRC2
        ObjectInfo(Nom)
    )],

    # adminIncidence2
    [ObjectInfo(Count), R2(Obj, Count)]
)])
