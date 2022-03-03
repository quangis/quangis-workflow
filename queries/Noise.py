# Noise
# 1. What is the proportion of noise ≥ 70dB in Amsterdam?

from config import REPO  # type: ignore
from transformation_algebra.type import _
from transformation_algebra.query import Query, AND, STEPS
from cct import cct, ObjectInfo, R2, Obj, Reg, Nom, Ratio, Ord, Loc, apply, ratio, groupbyLR, size, pi1  # type: ignore

workflows = {
    REPO.NoisePortionAmsterdam,
    REPO.NoiseProPortionAmsterdam,
    REPO.NoiseProPortionAmsterdam2}

query = Query(cct,
    [ObjectInfo(Ratio), apply, AND(
        ratio,
        [groupbyLR, AND(size, STEPS(pi1, R2(Loc, _)))],
        [apply, AND(size, R2(Obj, Reg))]
    )]
)
