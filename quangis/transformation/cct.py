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
R1 = TypeOperator.parameterized("R1", 1)  # Collections
R2 = TypeOperator.parameterized("R2", 2)  # Unary core concepts
R3 = TypeOperator.parameterized("R3", 3)  # Quantified relations

SpatialField = R2(Loc, Qlt)
InvertedField = R2(Qlt, Reg)
FieldSample = R2(Reg, Qlt)
ObjectExtent = R2(Obj, Reg)
ObjectQuality = R2(Obj, Qlt)
NominalField = R2(Loc, Nom)
BooleanField = R2(Loc, Bool)
NominalInvertedField = R2(Nom, Reg)
BooleanInvertedField = R2(Bool, Reg)

##############################################################################
# Data inputs

cct.pointmeasures = R2(Reg, Itv), 1
cct.amountpatches = R2(Reg, Nom), 1
cct.contour = R2(Ord, Reg), 1
cct.objects = R2(Obj, Ratio), 1
cct.objectregions = R2(Obj, Reg), 1
cct.contourline = R2(Itv, Reg), 1
cct.objectcounts = R2(Obj, Count), 1
cct.field = R2(Loc, Ratio), 1
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
cct.count = R1(Obj) ** Ratio
cct.size = R1(Loc) ** Ratio
cct.merge = R1(Reg) ** Reg
cct.centroid = R1(Loc) ** Loc

# statistical operations
cct.avg = R2(var.v, Itv) ** Itv, var.v.subtype(Val)
cct.min = R2(var.v, Ord) ** Ord, var.v.subtype(Val)
cct.max = R2(var.v, Ord) ** Ord, var.v.subtype(Val)
cct.sum = R2(var.v, Count) ** Count, var.v.subtype(Val)

###########################################################################
# Geographic transformations

cct.intersect = R1(Loc) ** R1(Loc) ** R1(Loc)

# conversions
cct.reify = R1(Loc) ** Reg
cct.deify = Reg ** R1(Loc)
cct.get = R1(var.x) ** var.x, var.x.subtype(Val)
cct.invert = R2(Loc, var.x) ** R2(Reg, var.x), var.x.subtype(Nom)
cct.invert2 = R2(Loc, Ord) ** R2(Ord, Reg)
cct.revert = R2(Reg, var.x) ** R2(Loc, var.x), var.x.subtype(Nom)
cct.revert2 = R2(Ord, Reg) ** R2(Loc, Ord)

# quantified relations
cct.oDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
cct.lDist = R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
cct.loDist = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj)
cct.oTopo = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj)
cct.loTopo = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj)
cct.nDist = R1(Obj) ** R1(Obj) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj)
cct.lVis = R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)
cct.interpol = R2(Reg, Itv) ** R1(Loc) ** R2(Loc, Itv)

# amount operations
cct.fcont = R2(Loc, Itv) ** Ratio
cct.ocont = R2(Obj, Ratio) ** Ratio

###########################################################################
# Relational transformations

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection.
cct.pi1 = var.rel ** R1(var.x), var.rel.param(var.x, at=1)
cct.pi2 = var.rel ** R1(var.x), var.rel.param(var.x, at=2)
cct.pi3 = var.rel ** R1(var.x), var.rel.param(var.x, at=3)

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
    var.rel ** R1(var.x) ** var.rel,
    var.rel.param(var.x)
)

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
cct.join_key = (
    R3(var.x, var.q1, var.y) ** var.rel ** R3(var.x, var.q2, var.y),
    var.rel.member(R2(var.x, var.q2), R2(var.y, var.q2))
)

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa.
# See: compose join_with1 (compose (compose reify (intersect (deify region 1)))) deify
cct.join_with1 = (
    (var.x1 ** var.x2)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2)
)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
cct.join_with2 = (
    (var.x1 ** var.x2 ** var.x3)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2) ** R2(var.y, var.x3)
)

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
cct.groupbyL = (
    (var.rel ** var.q2) ** R3(var.l, var.q1, var.r) ** R2(var.l, var.q2),
    var.rel.member(R1(var.r), R2(var.r, var.q1))
)

cct.groupbyR = (
    (var.rel ** var.q2) ** R3(var.l, var.q1, var.r) ** R2(var.r, var.q2),
    var.rel.member(R1(var.l), R2(var.l, var.q1))
)
