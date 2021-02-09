"""
Module containing the core concept transformation algebra. Usage:

    >>> from quangis import cct
    >>> expr = cct.parse("pi1 (objects data)")
    >>> print(expr.type)
    R(Obj)
"""

from quangis.transformation.type import TypeOperator, Variables
from quangis.transformation.algebra import TransformationAlgebra

cct = TransformationAlgebra()
var = Variables()

##############################################################################
# Types and type synonyms

Val = TypeOperator("Val")
Obj = TypeOperator("Obj", supertype=Val)  # O
Reg = TypeOperator("Reg", supertype=Val)  # S
Loc = TypeOperator("Loc", supertype=Val)  # L
Qlt = TypeOperator("Qlt", supertype=Val)  # Q
Nom = TypeOperator("Nom", supertype=Qlt)
Bool = TypeOperator("Bool", supertype=Nom)
Ord = TypeOperator("Ord", supertype=Nom)
Itv = TypeOperator("Itv", supertype=Ord)
Ratio = TypeOperator("Ratio", supertype=Itv)
Count = TypeOperator("Count", supertype=Ratio)
R = TypeOperator.R

SpatialField = R(Loc, Qlt)
InvertedField = R(Qlt, Reg)
FieldSample = R(Reg, Qlt)
ObjectExtent = R(Obj, Reg)
ObjectQuality = R(Obj, Qlt)
NominalField = R(Loc, Nom)
BooleanField = R(Loc, Bool)
NominalInvertedField = R(Nom, Reg)
BooleanInvertedField = R(Bool, Reg)

##############################################################################
# Data inputs

cct.pointmeasures = R(Reg, Itv), 1
cct.amountpatches = R(Reg, Nom), 1
cct.contour = R(Ord, Reg), 1
cct.objects = R(Obj, Ratio), 1
cct.objectregions = R(Obj, Reg), 1
cct.contourline = R(Itv, Reg), 1
cct.objectcounts = R(Obj, Count), 1
cct.field = R(Loc, Ratio), 1
cct.object = Obj, 1
cct.region = Reg, 1
cct.in_ = Nom, 0
cct.countV = Count, 1
cct.ratioV = Ratio, 1
cct.interval = Itv, 1
cct.ordinal = Ord, 1
cct.nominal = Nom, 1

###########################################################################
# Math/stats transformations

# functional
cct.compose = (var.y ** var.z) ** (var.x ** var.y) ** (var.x ** var.z)
cct.swap = (var.x ** var.y ** var.z) ** (var.y ** var.x ** var.z)
cct.cast = var.x ** var.y, var.x.subtype(var.y)

# derivations
cct.ratio = Ratio ** Ratio ** Ratio
cct.leq = var.x ** var.x ** Bool, var.x.subtype(Ord)
cct.eq = var.x ** var.x ** Bool, var.x.subtype(Val)

# aggregations of collections
cct.count = R(Obj) ** Ratio
cct.size = R(Loc) ** Ratio
cct.merge = R(Reg) ** Reg
cct.centroid = R(Loc) ** Loc

# statistical operations
cct.avg = R(var.v, Itv) ** Itv, var.v.subtype(Val)
cct.min = R(var.v, Ord) ** Ord, var.v.subtype(Val)
cct.max = R(var.v, Ord) ** Ord, var.v.subtype(Val)
cct.sum = R(var.v, Count) ** Count, var.v.subtype(Val)

###########################################################################
# Geographic transformations

cct.intersect = R(Loc) ** R(Loc) ** R(Loc)

# conversions
cct.reify = R(Loc) ** Reg
cct.deify = Reg ** R(Loc)
cct.get = R(var.x) ** var.x, var.x.subtype(Val)
cct.invert = R(Loc, var.x) ** R(Reg, var.x), var.x.subtype(Nom)
cct.invert2 = R(Loc, Ord) ** R(Ord, Reg)
cct.revert = R(Reg, var.x) ** R(Loc, var.x), var.x.subtype(Nom)
cct.revert2 = R(Ord, Reg) ** R(Loc, Ord)

# quantified relations
cct.oDist = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Ratio, Obj)
cct.lDist = R(Loc) ** R(Loc) ** R(Loc, Ratio, Loc)
cct.loDist = R(Loc) ** R(Obj, Reg) ** R(Loc, Ratio, Obj)
cct.oTopo = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Nom, Obj)
cct.loTopo = R(Loc) ** R(Obj, Reg) ** R(Loc, Nom, Obj)
cct.nDist = R(Obj) ** R(Obj) ** R(Obj, Ratio, Obj) ** R(Obj, Ratio, Obj)
cct.lVis = R(Loc) ** R(Loc) ** R(Loc, Itv) ** R(Loc, Bool, Loc)
cct.interpol = R(Reg, Itv) ** R(Loc) ** R(Loc, Itv)

# amount operations
cct.fcont = R(Loc, Itv) ** Ratio
cct.ocont = R(Obj, Ratio) ** Ratio

###########################################################################
# Relational transformations

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection.
cct.pi1 = var.rel ** R(var.x), var.rel.param(var.x, at=1)
cct.pi2 = var.rel ** R(var.x), var.rel.param(var.x, at=2)
cct.pi3 = var.rel ** R(var.x), var.rel.param(var.x, at=3)

# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.
cct.select = (
    (var.x ** var.y ** Bool) ** var.rel ** var.y ** var.rel,
    var.rel.param(var.x, subtype=True)
)

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
cct.join_subset = (
    var.rel ** R(var.x) ** var.rel,
    var.rel.param(var.x)
)

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
cct.join_key = (
    R(var.x, var.q1, var.y) ** var.rel ** R(var.x, var.q2, var.y),
    var.rel.member(R(var.x, var.q2), R(var.y, var.q2))
)

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa.
# See: compose join_with1 (compose (compose reify (intersect (deify region 1)))) deify
cct.join_with1 = (
    (var.x1 ** var.x2)
    ** R(var.y, var.x1) ** R(var.y, var.x2)
)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
cct.join_with2 = (
    (var.x1 ** var.x2 ** var.x3)
    ** R(var.y, var.x1) ** R(var.y, var.x2) ** R(var.y, var.x3)
)

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
cct.groupbyL = (
    (var.rel ** var.q2) ** R(var.l, var.q1, var.r) ** R(var.l, var.q2),
    var.rel.member(R(var.r), R(var.r, var.q1))
)

cct.groupbyR = (
    (var.rel ** var.q2) ** R(var.l, var.q1, var.r) ** R(var.r, var.q2),
    var.rel.member(R(var.l), R(var.l, var.q1))
)
