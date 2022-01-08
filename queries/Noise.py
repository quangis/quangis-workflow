# Noise
# 1. What is the proportion of noise ≥ 70dB in Amsterdam?

from config import REPO  # type: ignore
from transformation_algebra.type import _
from transformation_algebra.query import Query, AND, LINKED
from cct import cct, R3a, R2, Obj, Reg, Nom, Ratio, Ord, Loc, apply, ratio, groupbyLR, size, pi1  # type: ignore

workflows = {
    REPO.NoisePortionAmsterdam,
    REPO.NoiseProPortionAmsterdam,
    REPO.NoiseProPortionAmsterdam2}

query = Query(cct,
    [R3a(Obj, Reg, Ratio), apply, AND(
        ratio,
        [groupbyLR, AND(size, LINKED(pi1, R2(Loc, _)))],
        [apply, AND(size, R2(Obj, Reg))]
    )]
)


# Evaluation #################################################################

# noisePortionAmsterdam

eval_noisePortionAmsterdam = Query(cct, [R2(Ord, Reg), R2(Loc, Ord), AND(
    [R2(Loc, Ord), R2(Ord, Reg)],
    R3a(Obj, Reg, Nom)
)])

# noiseProPortionAmsterdam:
# output: R3a(Obj, Reg, Ratio) #
# input: R3a(Obj, Reg, Nom) #cbs buurten
# input: R2(Ord, Reg)       #noise

eval_noiseProPortionAmsterdam = Query(cct,
    [R3a(Obj, Reg, Ratio), R2(Obj, Ratio), AND(
        # size of object regions
        [R2(Obj, Ratio), R3a(Obj, Reg, Nom)],

        # size of noise regions in object
        [R2(Obj, Ratio), R2(Loc, Ord), R2(Ord, Reg)]
    )]
)

# noiseProPortionAmsterdam2:

eval_noiseProPortionAmsterdam2 = Query(cct,
    [R3a(Obj, Reg, Ratio), R2(Obj, Ratio), AND(
        # size of object regions
        [R2(Obj, Ratio), R3a(Obj, Reg, Nom)],

        # size of noise regions in object
        [R2(Obj, Ratio), R2(Loc, Ord), R2(Ord, Reg)]
    )]
)
