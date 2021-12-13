from ..cct import AND, R3a, R2, R3, Obj, Reg, Nom, Ratio, Loc  # type: ignore

# Eric
# input: R3a(Obj, Nom, Reg)
# input: R2(Ratio, Reg)
# input: R3(Obj, Nom, Reg)
# input: R3(Obj, Ratio, Reg)
# output: R3a(Obj, Nom, Reg)

eval_aquifer_eric = [R3a(Obj, Nom, Reg), AND(
    # UrbanAreas3
    [AND(

        # UrbanAreas2
        [AND(

            # aquifer2
            [R2(Obj, Reg), R3a(Obj, Nom, Reg)],

            # urbanAreas
            R3a(Obj, Nom, Reg)
        )],

        # precipitation2
        R2(Ratio, Reg)
    )],

    # irrigation2
    R3(Obj, Ratio, Reg)
)]

# Simon
# input: R3a(Obj, Reg, Nom) #aquifer
# input: R3a(Obj, Reg, Nom) #urban areas
# input: R2(Nom, Reg) #precipitation coverage
# input: R2(Nom, Reg) #irrigation coverage

eval_aquifer_simon = [R3a(Obj, Reg, Nom), AND(
    [R2(Obj, Reg), R3a(Obj, Reg, Nom)],  # urban areas
    [R2(Obj, Reg), R3a(Obj, Reg, Nom)],  # aquifer
    [R2(Loc, Nom), R2(Nom, Reg)],  # precipitation coverage
    [R2(Loc, Nom), R2(Nom, Reg)]  # irrigation coverage
)]
