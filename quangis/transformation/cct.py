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

# derivations
cct.ratio = Ratio ** Ratio ** Ratio
cct.leq = Ord ** Ord ** Bool
cct.eq = Val ** Val ** Bool

# aggregations of collections
cct.count = R(Obj) ** Ratio
cct.size = R(Loc) ** Ratio
cct.merge = R(Reg) ** Reg
cct.centroid = R(Loc) ** Loc

# statistical operations
cct.avg = R(Val, Itv) ** Itv
cct.min = R(Val, Ord) ** Ord
cct.max = R(Val, Ord) ** Ord
cct.sum = R(Val, Count) ** Count

###########################################################################
# Geographic transformations

cct.intersect = R(Loc) ** R(Loc) ** R(Loc)

# conversions
cct.reify = R(Loc) ** Reg
cct.deify = Reg ** R(Loc)
cct.get = R(var.x) ** var.x, var.x.limit(Val)
cct.invert = \
    R(Loc, Ord) ** R(Ord, Reg), \
    R(Loc, Nom) ** R(Reg, Nom)
cct.revert = \
    R(Ord, Reg) ** R(Loc, Ord), \
    R(Reg, Nom) ** R(Loc, Nom)

# quantified relations
cct.oDist = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Ratio, Obj)
cct.lDist = R(Loc) ** R(Loc) ** R(Loc, Ratio, Loc)
cct.loDist = R(Loc) ** R(Obj, Reg) ** R(Loc, Ratio, Obj)
cct.oTopo = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Nom, Obj)
cct.loTopo = R(Loc) ** R(Obj, Reg) ** R(Loc, Nom, Obj)
cct.nDist = R(Obj) ** R(Obj) ** R(Obj, Ratio, Obj) ** R(Obj, Ratio, Obj)
cct.lVis = R(Loc) ** R(Loc) ** R(Loc, Itv) ** R(Loc, Bool, Loc)
cct.interpol = R(Reg, Itv) ** R(Loc) ** R(Loc, Itv)
cct.extrapol = R(Obj, Reg) ** R(Loc, Bool) #Buffering

# amount operations
cct.fcont = R(Loc, Itv) ** Ratio
cct.ocont = R(Obj, Ratio) ** Ratio

###########################################################################
# Relational transformations

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection.
cct.pi1 = var.rel ** R(var.x), var.rel.has_param(R, var.x, at=1)
cct.pi2 = var.rel ** R(var.x), var.rel.has_param(R, var.x, at=2)
cct.pi3 = var.rel ** R(var.x), var.rel.has_param(R, var.x, at=3)

# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.
cct.select = (var.x ** var.x ** Bool) ** var.rel ** var.x ** var.rel, \
    var.x.limit(Val), var.rel.has_param(R, var.x)

# Join (⨝). Subset a relation to those tuples having an attribute value
# contained in a collection. Used to be bowtie.
cct.join_subset = var.rel ** R(var.x) ** var.rel, \
    var.x.limit(Val), var.rel.has_param(R, var.x)

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
cct.join_key = R(var.x, Qlt, var.y) ** var.rel ** R(var.x, var.q, var.y), \
    var.x.limit(Val), var.y.limit(Val), var.q.limit(Qlt), \
    var.rel.limit(R(var.x, var.q), R(var.y, var.q))

# Join with unary function. Generate a unary concept from one 
# See: compose join_fa (compose (compose reify (intersect (deify region 1)))) deify
cct.join_fa = (var.x ** var.y) ** R(var.z, var.x) ** R(var.z, var.y)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
cct.join_with = (var.q1 ** var.q1 ** var.q2) ** R(var.x, var.q1) ** R(var.x, var.q1) ** R(var.x, var.q2), \
    var.q1.limit(Qlt), var.q2.limit(Qlt), var.x.limit(Val)

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
cct.groupbyL = (var.rel ** var.q) ** R(var.x, var.q, var.y) ** R(var.x, var.q), \
    var.x.limit(Val), var.y.limit(Val), \
    var.q.limit(Qlt), \
    var.rel.limit(R(var.x), R(var.x, var.q))

cct.groupbyR = (var.rel ** var.q) ** R(var.x, var.q, var.y) ** R(var.y, var.q), \
    var.x.limit(Val), var.y.limit(Val), \
    var.q.limit(Qlt), \
    var.rel.limit(R(var.y), R(var.y, var.q))
