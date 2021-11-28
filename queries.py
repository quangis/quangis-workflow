#!/usr/bin/env python3
"""
These are the queries from the transformation algebra paper, translated to
Python.
"""

from __future__ import annotations

from transformation_algebra.type import _
from transformation_algebra.query import Query, AND, OR, Operators
from cct import CCT, R2, R3a, Obj, Reg, Bool, Ratio, Loc, Count, Itv, Nom, Ord, \
    apply, ratio, groupbyR, size, pi1, count, avg, min, nDist, extrapol, \
    product, select, loTopo, oDist, lgDist, max, flowdirgraph, accumulate, \
    groupbyL, sum, loDist, lgDist, lDist

groupby: Operators = OR(groupbyR, groupbyL)
dist: Operators = OR(nDist, loDist, lgDist, lDist, oDist)

# 1. (Noise) What is the proportion of noise ≥ 70dB in Amsterdam?
noiseProPortionAmsterdam = Query(CCT,
    [R3a(Obj, Reg, Ratio), ..., apply, AND(
        [..., ratio],
        [..., groupby, AND([..., size], [..., pi1, R2(Loc, _)])],
        [..., apply, AND([..., size], [..., R2(Obj, Reg)])]
    )]
)

# 2. (Population) What is the number of inhabitants for each neighbourhood in
# Utrecht?
amountObjectsUtrecht = Query(CCT,
    [R3a(Obj, Reg, Count), OR(
        [groupby, AND([..., sum], [..., R2(Reg, Count)])],
        [groupby, AND([..., count], [..., R2(Obj, Reg)])]
    )]
)

# 3. (Temperature) What is the average temperature for each neighbourhood in
# Utrecht?
amountFieldUtrecht = Query(CCT,
    [R3a(Obj, Reg, Itv), ..., groupby, AND(
        [..., avg],
        [..., R2(Loc, Itv)]
    )]
)

# 4. What is the travel distance to the nearest hospital in California?
hospital_accessibility = Query(CCT,
    [R3a(Obj, Reg, Ratio), ..., groupby, AND(
        [..., min],
        [..., nDist],
        [..., R2(Obj, Reg)]
    )]
)

# 5. What is the impact of roads on deforestation in the Amazon rainforest?
# deforestation = Query(CCT,
#     [R2(Bool, Ratio), AND(
#         [..., size, pi1, ..., extrapol, R2(Obj, Reg)],
#         [..., size, pi1, ..., R2(Loc, _)]
#     )]
# )

# 6. What is the potential of solar power for each rooftop in the Glover Park
# neighbourhood in Washington DC?
solar = Query(CCT,
    [R3a(Obj, Reg, Ratio), ..., groupby, OR(
        [..., avg],
        [..., R2(Loc, Ratio)],
        [..., R2(Obj, Reg)]
    )]
)

# 7. (Road-Access) What is the percentage of rural population within 2km
# distance to all-season roads in Shikoku, Japan?
# infrastructureAccess = Query(CCT,
#     [R2(Reg, Ratio), AND(
#         [..., ratio],
#         [..., R2(Reg, Ratio), ..., AND(
#             [..., extrapol, R2(Obj, Reg)],
#             [..., R2(Reg, Count)]
#         )]
#     )]
# )

# 8. (Water-risk) Which urban areas are at risk from water depletion in
# Ogandala (High Plains) Aquifer, US?
# aquifer = Query(CCT,
#     [R3a(Obj, Reg, Nom), ..., AND(
#         [..., select, ..., loTopo, AND(
#             [..., pi1, ..., R2(Loc, Nom)],
#             [..., select, ..., oDist, ..., R2(Obj, Reg)]
#         ]))
#     ])
# )

# 9. What is the stream runoff during a predicted rainstorm in Vermont, US?
floods = Query(CCT,
    [R2(Ord, Ratio), ..., groupby, AND(
        [..., size],
        [..., R2(Loc, Ord), ..., groupby, AND(
            [..., max],
            [..., accumulate, ..., flowdirgraph, ..., R2(Loc, Itv)],
            [..., lgDist]
        )]
    )]
)

# 10. What is the malaria incidence rate per 1000 inhabitants in the Democratic
# Republic of the Congo?
malaria = Query(CCT,
    [R3a(Obj, Reg, Ratio), AND(
        [..., ratio],
        [..., R2(Obj, Count)],
        [..., R2(Obj, Count), groupby, AND(
            [..., sum],
            [..., R2(Reg, Count)]
        )]
    )]
)
