from ..cct import AND, R3a, R1, R2, Obj, Reg, Nom, Ratio, Loc, Bool  # type: ignore

# Eric
# R3a(Obj, Nom, Reg)  # roads
# R2(Obj, Nom, Reg)  # planned
# R3a(Obj, Nom, Reg)  # deforested

eval_deforestation_eric = [R2(Reg, Ratio), AND(

    # Erasedbuffer2
    [R2(Reg, Ratio), AND(

        # plannedroadbuffer
        [R1(Reg), R1(Reg)],

        # deforested
        R1(Reg)
    )],

    # areaPercentage
    [AND(

        # roadsBuffer2
        [R2(Reg, Ratio), R1(Reg), R3a(Obj, Nom, Reg)],

        # deforestedRoadArea
        [AND(

            # deforested
            R3a(Obj, Nom, Reg),

            # roadsbuffer
            [R1(Reg), R3a(Obj, Nom, Reg)]
        )]
    )]
)]

# Simon
# R3a(Obj, Reg, Nom)  # roads
# R3a(Obj, Reg, Nom)  # planned
# R2(Loc, Bool) # deforested area

# size of deforested area within buffer area
eval_deforestation_simon = [R2(Bool, Ratio), AND(

    # erased buffer
    [R2(Loc, Bool), AND(
        [R2(Loc, Bool)],  # deforested area
        [R2(Loc, Bool), R3a(Obj, Reg, Nom)]  # planned road buffer
    )],

    # proportion
    [R2(Bool, Ratio), AND(

        # deforested region within buffer
        [R1(Loc), R2(Loc, Bool), AND(
            [R2(Loc, Bool)],  # deforested area
            [R2(Loc, Bool), R3a(Obj, Reg, Nom)]  # roads buffer
        )],

        # region of roads buffer
        [R1(Loc), R2(Loc, Bool), R3a(Obj, Reg, Nom)]
    )]
)]
