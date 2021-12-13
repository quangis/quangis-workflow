from ..cct import AND, R3a, R2, R3, Obj, Reg, Nom, Ratio, Loc  # type: ignore

# hospitalsNear

# input R3a(Obj, Nom, Reg)  # roads
# input R2(Obj, Loc)  # hospital points
# input R2(Obj, Loc)  # incident location

eval_hospitalsnear_eric = [R2(Obj, Loc), AND(
    R3a(Obj, Nom, Reg),
    R2(Obj, Loc),
    R2(Obj, Loc)
)]

# --------------------------------------------
# hospitalsNetwork

# input R3a(Obj, Nom, Reg)  # roads
# input R2(Obj, Loc)  # hospital points
# input R2(Obj,  Loc)  # incident location

eval_hospitalsnetwork_eric = [R2(Obj, Nom), R3a(Obj, Nom, Obj), AND(
    R3a(Obj, Nom, Reg),
    R2(Obj, Loc),
    R2(Obj, Loc)
)]

# ------------------
# simon:
# hospitalsNear

# input R3a(Obj, Reg, Nom)  # hospital points
# input R3a(Obj, Reg, Nom)  # incident location

eval_hospitalsnear_simon = [R2(Obj, Ratio), R3(Obj, Ratio, Obj), AND(
    [R3a(Obj, Reg, Nom)],
    [R3a(Obj, Reg, Nom)]
)]


# hospitalsNetwork

# input R3a(Obj, Reg, Nom)  # Roads
# input R3a(Obj, Reg, Nom)  # Hospital points
# input R3a(Obj, Reg, Nom)  # Incident location

eval_hospitalsnetwork_simon = [R2(Obj, Ratio), R3(Obj, Ratio, Obj), AND(
    [R3a(Obj, Reg, Nom)],
    [R3a(Obj, Reg, Nom)],
    [R3a(Obj, Reg, Nom)]
)]
