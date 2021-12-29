# Malaria
# 10. What is the malaria incidence rate per 1000 inhabitants in the Democratic
# Republic of the Congo?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import CCT, R3a, R2, Obj, Reg, Nom, Count, Ratio, ratio, sum, groupbyLR  # type: ignore

workflows = {REPO.Malaria}

malaria = Query(CCT,
    [R3a(Obj, Reg, Ratio), AND(
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

eval_malaria_eric = Query(CCT, [R2(Obj, Ratio), AND(
    # adminDRC3
    AND(

        # adminDRC2
        R3a(Obj, Nom, Reg),

        # popAdminDRC
        [R3a(Obj, Ratio, Reg), AND(

            # population
            R2(Reg, Ratio),

            # adminDRC2
            R3a(Obj, Nom, Reg)
        )]
    ),

    # adminIncidence2
    R2(Obj, Ratio)
)])

# simon

eval_malaria_simon = Query(CCT, [R3a(Obj, Reg, Ratio), AND(

    # popAdminDRC
    [R3a(Obj, Reg, Count), AND(

        # population on cells
        R2(Reg, Count),

        # adminDRC2
        R3a(Obj, Reg, Nom)
    )],

    # adminIncidence2
    [R3a(Obj, Reg, Count), R2(Obj, Count)]
)])
