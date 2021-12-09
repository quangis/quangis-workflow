from ..cct import AND, R3a, R1, R2, Obj, Reg, Nom, Ord, Count, Ratio, Loc, Bool  # type: ignore

# R3a(Obj, Ord, Reg)  # urbanization
# R3a(Obj, Ratio, Reg)  # chochomoku
# R2(Obj, Reg)  # roads

eval_infrastructure_eric = [R1(Ratio), ..., AND(

    # rural_pop2
    [R3a(Obj, Ratio, Reg), R2(Obj, Reg), AND(

        # chochomoku
        R3a(Obj, Ratio, Reg),

        # rural
        [R2(Obj, Reg), R3a(Obj, Ord, Reg)]
    )],

    # rural_access1
    [R2(Reg, Ratio), ..., AND(

        # rural_clip
        [R2(Reg, Ratio), R2(Obj, Reg), R3a(Obj, Ord, Reg)],

        # roads_buffer
        [R1(Reg), R2(Obj, Reg)]
    )]
)]

# ------------------------------------
# simon:

# count amount ratio
eval_infrastructure_simon = [R2(Reg, Ratio), ..., AND(

    # rural clip and summing contentamount (rural_pop1)
    (R2(Reg, Count), ..., R3a(Obj, Reg, Count), ..., AND(

        # chochomoku
        [..., R3a(Obj, Reg, Count)],

        # rural
        [R2(Obj, Reg), ..., R3a(Obj, Reg, Nom)]
    )),

    # rural_access1 via areal interpolation
    [R2(Reg, Count), ..., AND(

        # rural_clip
        [..., R3a(Obj, Reg, Count), ..., AND(

            # chochomoku
            [..., R3a(Obj, Reg, Count)],

            # rural
            [R2(Obj, Reg), ..., R3a(Obj, Reg, Nom)]
        )],

        # roads_buffer
        [..., R2(Loc, Bool), ..., R2(Obj, Reg, Nom)]
    )]
)]
