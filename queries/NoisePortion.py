# Noise
# 1. What is the proportion of noise ≥ 70dB in Amsterdam?

from config import REPO  # type: ignore
from transformation_algebra.query import Query, AND
from cct import cct, R3a, R2, Obj, Reg, Nom, Ord, Loc  # type: ignore

workflows = {REPO.NoisePortionAmsterdam}

# Evaluation #################################################################

# noisePortionAmsterdam

eval_noisePortionAmsterdam = Query(cct, [R2(Ord, Reg), R2(Loc, Ord), AND(
    [R2(Loc, Ord), R2(Ord, Reg)],
    R3a(Obj, Reg, Nom)
)])
