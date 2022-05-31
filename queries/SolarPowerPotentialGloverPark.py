# Solar
# 6. What is the potential of solar power for each rooftop in the Glover Park
# neighbourhood in Washington DC?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND, OR
from cct import cct, ObjectInfo, R2, Obj, Reg, Nom, Ratio, Loc, Itv, groupbyLR, avg  # type: ignore

workflows = {REPO.SolarPowerPotentialGloverPark}

query = Query(cct,
    [ObjectInfo(Ratio), groupbyLR, OR(
        avg,
        R2(Loc, Ratio),
        R2(Obj, Reg)
    )]
)


# Evaluation #################################################################

# solar power potential of rooftops

# inputs: dsm: R2(L, Itv)
# inputs: solarRad: R2(L, Ratio)
# inputs: buildings: R3a(Obj, Reg, Nom)

# usable radiation per building
eval_solar = Query(cct, [ObjectInfo(Ratio), R2(Obj, Ratio), AND(

    # average radiation
    [R2(Obj, Ratio), AND(

        # usable radiation
        [R2(Loc, Ratio), AND(
            [R2(Loc, Itv)],  # dsm
            [R2(Loc, Ratio)]  # solar radiation
        )],

        # buildings
        [ObjectInfo(Nom)]
    )],

    # usable building area size
    [R2(Obj, Ratio), ObjectInfo(Nom)]
)])