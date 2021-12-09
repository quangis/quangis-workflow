# average temperature in Utrecht

# input cbsneighbours: R3a(Obj, Reg, Nom)
# input weather stations: R2(Reg, Itv)

[R3a(Obj, Reg, Itv), ...,  R2(Obj, Itv), AND(
    [..., R2(L, Itv), ..., R2(Reg, Itv)],
    [..., R2(Obj, Reg), ..., R3a(Obj, Reg, Nom)]
)]
