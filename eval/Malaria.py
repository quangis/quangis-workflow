from ..cct import AND, R3a, R2, Obj, Reg, Nom, Count, Ratio  # type: ignore

# R3a(Obj, Nom, Reg)  # countries
# R3a(Obj, Nom, Reg)  # adminRegions
# R2(Reg, Ratio)  # population
# R2(Obj, Ratio)  # countryIncidence
# R2(Obj, Ratio)  # adminIncidence

eval_malaria_eric = [R2(Obj, Ratio), ..., AND(
    # adminDRC3
    [..., AND(

        # adminDRC2
        R3a(Obj, Nom, Reg),

        # popAdminDRC
        [R3a(Obj, Ratio, Reg), ..., AND(

            # population
            R2(Reg, Ratio),

            # adminDRC2
            R3a(Obj, Nom, Reg)
        )]
    )],

    # adminIncidence2
    R2(Obj, Ratio)
)]

# simon

eval_malaria_simon = [R3a(Obj, Reg, Ratio), ..., AND(

    # popAdminDRC
    [R3a(Obj, Reg, Count), ..., AND(

        # population on cells
        R2(Reg, Count),

        # adminDRC2
        R3a(Obj, Reg, Nom)
    )],

    # adminIncidence2
    [R3a(Obj, Reg, Count), ..., R2(Obj, Count)]
)]
