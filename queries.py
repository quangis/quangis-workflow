"""
These are the queries from the transformation algebra paper, translated to
Python.
"""

from transformation_algebra.type import _
from transformation_algebra.flow import Flow
from cct import R2, R3a, Obj, Reg, Bool, Ratio, Loc, Count, Itv, Nom, Ord, \
    apply, ratio, groupbyR, size, pi1, count, avg, min, nDist, extrapol, \
    product, select, loTopo, lgDist, max, flowdirgraph, accumulate

groupby = groupbyR  # Temporary solution
dist = nDist  # Temporary solution
TransformationQuery = Flow.serial  # Temporary name

# 1. What is the proportion of noise ≥ 70dB in Amsterdam?
noise = TransformationQuery(
    R3a(Obj, Reg, Ratio), ..., apply, [
        (..., ratio),
        (..., groupby, [(..., size), (..., pi1, R2(Loc, _))]),
        (..., apply, [(..., size), (..., R2(Obj, Reg))])
    ]
)

# 2. What is the number of inhabitants for each neighbourhood in Utrecht?
population = TransformationQuery(
    R3a(Obj, Reg, Count), [  # TODO replace when choice feature is implemented
        (groupby, [(..., sum), (..., R2(Reg, Count))]),
        (groupby, [(..., count), (..., R2(Obj, Reg))])
    ]
)

# 3. What is the average temperature for each neighbourhood in Utrecht?
temperature = TransformationQuery(
    R3a(Obj, Reg, Itv), ..., groupby, [
        (..., avg),
        (..., R2(Loc, Itv))
    ]
)

# 4. What is the travel distance to the nearest hospital in California?
hospital_accessibility = TransformationQuery(
    R3a(Obj, Reg, Ratio), ..., groupby, [
        (..., min),
        (..., dist, R2(Obj, Reg))
    ]
)

# 5. What is the impact of roads on deforestation in the Amazon rainforest?
deforestation = TransformationQuery(
    R2(Bool, Ratio), ..., size, pi1, ..., extrapol, R2(Obj, Reg)
)

# 6. What is the potential of solar power for each rooftop in the Glover Park
# neighbourhood in Washington DC?
solar_power = TransformationQuery(
    R3a(Obj, Reg, Ratio), [
        (..., avg),
        (..., R2(Loc, Ratio), ..., groupby, apply, [
            (..., size),
            (..., product)
        ])
    ]
)

# 7. What is the percentage of rural population within 2km distance to
# all-season roads in Shikoku, Japan?
road_access = TransformationQuery(
    R2(Reg, Ratio), [
        (..., ratio),
        (..., apply, R2(Reg, Count), ..., extrapol)
    ]
)

# 8. Which urban areas are at risk from water depletion in Ogallala (High
# Plains) Aquifer, US?
water_risk = TransformationQuery(
    R3a(Obj, Reg, Nom), [
        (..., select, ..., loTopo, ..., pi1, ..., R2(Loc, Nom)),
        (..., select, ..., dist, ..., R2(Obj, Reg))
    ]
)

# 9. What is the stream runoff during a predicted rainstorm in Vermont, US?
floods = TransformationQuery(
    R2(Ord, Ratio), ..., groupby, [
        (..., size),
        (..., R2(Loc, Ord), groupby, ..., accumulate, flowdirgraph, ..., [
            (..., lgDist),
            (..., max),
            (..., R2(Loc, Itv))
        ])
    ]
)

# 10. What is the malaria incidence rate per 1000 inhabitants in the Democratic
# Republic of the Congo?
malaria = TransformationQuery(
    R2(Obj, Reg, Ratio), [
        (..., ratio),
        (..., R2(Obj, Count)),
        (..., R2(Obj, Count), groupby, ..., sum, R2(Reg, Count))
    ]
)
