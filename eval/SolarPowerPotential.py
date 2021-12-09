# solar power potential of rooftops

# inputs: dsm: R2(L, Itv)
# inputs: solarRad: R2(L, Ratio)
# inputs: buildings: R3a(Obj, Reg, Nom)

# usable radiation per building
[R3a(Obj, Reg, Ratio), ...,  R2(Obj, Ratio), AND(

    # average radiation
    [..., R2(Obj, Ratio), AND(

        # usable radiation
        [...,  R2(L, Ratio), AND(
            [...,  R2(L, Itv)],  # dsm
            [...,  R2(L, Ratio)]  # solar radiation
        )],

        # buildings
        [...,  R3a(Obj, Reg, Nom)]
    )],

    # usable building area size
    [...,  R2(Obj, Ratio),  ...,  R3a(Obj, Reg, Nom)]
)]
