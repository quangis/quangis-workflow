# Noise
# 1. What is the proportion of noise ≥ 70dB in Amsterdam?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import cct, ObjectInfo, R2, Obj, Reg, Nom, Ratio, Ord, Loc  # type: ignore

workflows = {
    REPO.NoiseProPortionAmsterdam,
    REPO.NoiseProPortionAmsterdam2}

# noiseProPortionAmsterdam:
# output: R3a(Obj, Reg, Ratio) #
# input: R3a(Obj, Reg, Nom) #cbs buurten
# input: R2(Ord, Reg)       #noise

eval_noiseProPortionAmsterdam = Query(cct,
    [ObjectInfo(Ratio), R2(Obj, Ratio), AND(
        # size of object regions
        [R2(Obj, Ratio), ObjectInfo(Nom)],

        # size of noise regions in object
        [R2(Obj, Ratio), R2(Loc, Ord), R2(Ord, Reg)]
    )]
)

# noiseProPortionAmsterdam2:

eval_noiseProPortionAmsterdam2 = Query(cct,
    [ObjectInfo(Ratio), R2(Obj, Ratio), AND(
        # size of object regions
        [R2(Obj, Ratio), ObjectInfo(Nom)],

        # size of noise regions in object
        [R2(Obj, Ratio), R2(Loc, Ord), R2(Ord, Reg)]
    )]
)
