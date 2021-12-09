from ..cct import AND, R3a, R2, Obj, Reg, Nom, Ratio, Ord, Loc  # type: ignore

# noisePortionAmsterdam

[R2(Ord, Reg), ..., R2(Loc, Ord), AND(
    [..., R2(Loc, Ord), ..., R2(Ord, Reg)],
    [..., R3a(Obj, Reg, Nom)]
)]

# noiseProPortionAmsterdam:
# output: R3a(Obj, Reg, Ratio) #
# input: R3a(Obj, Reg, Nom) #cbs buurten
# input: R2(Ord, Reg)       #noise

[R3a(Obj, Reg, Ratio), ..., R2(Obj, Ratio), AND(
    # size of object regions
    [..., R2(Obj, Ratio), ..., R3a(Obj, Reg, Nom)],

    # size of noise regions in object
    [..., R2(Obj, Ratio), ..., R2(Loc, Ord), ..., R2(Ord, Reg)]
)]

# noiseProPortionAmsterdam2:

[R3a(Obj, Reg, Ratio), ..., R2(Obj, Ratio), AND(
    # size of object regions
    [..., R2(Obj, Ratio), ..., R3a(Obj, Reg, Nom)],

    # size of noise regions in object
    [..., R2(Obj, Ratio), ..., R2(Loc, Ord), ..., R2(Ord, Reg)]
)]
