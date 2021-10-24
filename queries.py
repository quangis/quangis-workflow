#!/usr/bin/env python3
"""
These are the queries from the transformation algebra paper, translated to
Python.
"""

from transformation_algebra.type import _
from transformation_algebra.query import TransformationQuery
from cct import CCT, R2, R3a, Obj, Reg, Bool, Ratio, Loc, Count, Itv, Nom, Ord, \
    apply, ratio, groupbyR, size, pi1, count, avg, min, nDist, extrapol, \
    product, select, loTopo, oDist, lgDist, max, flowdirgraph, accumulate, sum

groupby = groupbyR  # Temporary solution
dist = nDist  # Temporary solution

# 1. (Noise) What is the proportion of noise ≥ 70dB in Amsterdam?
noiseProPortionAmsterdam = TransformationQuery(
    R3a(Obj, Reg, Ratio), ..., apply, [
        (..., ratio),
        (..., groupby, [(..., size), (..., pi1, R2(Loc, _))]),
        (..., apply, [(..., size), (..., R2(Obj, Reg))])
    ],
    namespace=CCT
)

# 2. (Population) What is the number of inhabitants for each neighbourhood in
# Utrecht?
# amountObjectsUtrecht = TransformationQuery(
#     R3a(Obj, Reg, Count), Choice(
#         (groupby, [(..., sum), (..., R2(Reg, Count))]),
#         (groupby, [(..., count), (..., R2(Obj, Reg))])
#     ),
#     namespace=CCT
# )

# 3. (Temperature) What is the average temperature for each neighbourhood in
# Utrecht?
amountFieldUtrecht = TransformationQuery(
    R3a(Obj, Reg, Itv), ..., groupby, [
        (..., avg),
        (..., R2(Loc, Itv))
    ],
    namespace=CCT
)

# 4. What is the travel distance to the nearest hospital in California?
hospital_accessibility = TransformationQuery(
    R3a(Obj, Reg, Ratio), ..., groupby, [
        (..., min),
        (..., nDist),
        (..., R2(Obj, Reg))
    ],
    namespace=CCT
)

# 5. What is the impact of roads on deforestation in the Amazon rainforest?
# deforestation = TransformationQuery(
#     R2(Bool, Ratio), [
#         (..., size, pi1, ..., extrapol, R2(Obj, Reg)),
#         (..., size, pi1, ..., R2(Loc, Nom))
#     ],
#     namespace=CCT
# )

# 6. What is the potential of solar power for each rooftop in the Glover Park
# neighbourhood in Washington DC?
solar = TransformationQuery(
    R3a(Obj, Reg, Ratio), ..., groupby, [
        (..., avg),
        (..., R2(Loc, Ratio)),
        (..., R2(Obj, Reg))
    ],
    namespace=CCT
)

# 7. (Road-Access) What is the percentage of rural population within 2km
# distance to all-season roads in Shikoku, Japan?
# infrastructureAccess = TransformationQuery(
#     R2(Reg, Ratio), [
#         (..., ratio),
#         (..., R2(Reg, Ratio), ..., [
#             (..., extrapol, R2(Obj, Reg)),
#             (..., R2(Reg, Count))
#         ])
#     ],
#     namespace=CCT
# )

# 8. (Water-risk) Which urban areas are at risk from water depletion in
# Ogallala (High Plains) Aquifer, US?
# aquifer = TransformationQuery(
#     R3a(Obj, Reg, Nom), ..., [
#         (..., select, ..., loTopo, [
#             (..., pi1, ..., R2(Loc, Nom)),
#             (..., select, ..., oDist, ..., R2(Obj, Reg))
#         ])
#     ],
#     namespace=CCT
# )

# 9. What is the stream runoff during a predicted rainstorm in Vermont, US?
floods = TransformationQuery(
    R2(Ord, Ratio), ..., groupby, [
        (..., size),
        (..., R2(Loc, Ord), ..., groupby, [
            (..., max),
            (..., accumulate, ..., flowdirgraph, ..., R2(Loc, Itv)),
            (..., lgDist)
        ])
    ],
    namespace=CCT
)

# 10. What is the malaria incidence rate per 1000 inhabitants in the Democratic
# Republic of the Congo?
malaria = TransformationQuery(
    R3a(Obj, Reg, Ratio), [
        (..., ratio),
        (..., R2(Obj, Count)),
        (..., R2(Obj, Count), groupby, [
            (..., sum),
            (..., R2(Reg, Count))
        ])
    ],
    namespace=CCT
)
