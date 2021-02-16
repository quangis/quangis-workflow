"""
Module containing the core concept transformation algebra. Usage:

    >>> from quangis.transformation.cct import cct
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
R2 = TypeOperator.parameterized("R2", 2)  # Unary core concepts, 1 key (left)
R3 = TypeOperator.parameterized("R3", 3)  # Quantified relation, 2 keys (l & r)
R3a = TypeOperator.parameterized("R3a", 3)  # Ternary relation, 1 key (left)

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
cct.countamounts = R2(Reg, Count), 1
cct.boolcoverages = R2(Bool, Reg), 1
cct.boolratio = R2(Bool, Ratio), 1
cct.nomcoverages = R2(Nom, Reg), 1
cct.nomsize = R2(Nom, Ratio), 1
cct.regions = R1(Reg), 1
cct.contour = R2(Ord, Reg), 1
cct.contourline = R2(Itv, Reg), 1
cct.objectregions = R2(Obj, Reg), 1
cct.objectregionratios = R3a(Obj, Reg, Ratio), 1
cct.objectregionnominals = R3a(Obj, Reg, Nom), 1
cct.objectregioncounts = R3a(Obj, Reg, Count), 1
cct.objectregionattr = R3a(Obj, Reg, var.x), 1
cct.field = R2(Loc, Ratio), 1
cct.nomfield = R2(Loc, Nom), 1
cct.boolfield = R2(Loc, Bool), 1
cct.ordfield = R2(Loc, Ord), 1
cct.itvfield = R2(Loc, Itv), 1
cct.ratiofield = R2(Loc, Ratio), 1
cct.object = Obj, 1
cct.objects = R1(Obj), 1
cct.region = Reg, 1
cct.in_ = Nom, 0
cct.out = Nom, 0
cct.noms = R1(Nom), 1
cct.ratios = R1(Ratio), 1
cct.countV = Count, 1
cct.ratioV = Ratio, 1
cct.interval = Itv, 1
cct.ordinal = Ord, 1
cct.nominal = Nom, 1
cct.true = Bool, 0

###########################################################################
# Math/stats transformations

# functional
cct.compose = (var.y ** var.z) ** (var.x ** var.y) ** (var.x ** var.z)
cct.compose2 = (var.y ** var.z) ** (var.w ** var.x ** var.y) ** (var.w ** var.x ** var.z)
cct.swap = (var.x ** var.y ** var.z) ** (var.y ** var.x ** var.z)
cct.id = var.x ** var.x
#cct.cast = var.x ** var.y, var.x.subtype(var.y)

# derivations
cct.ratio = Ratio ** Ratio ** Ratio
cct.product = Ratio ** Ratio ** Ratio
cct.leq = var.x ** var.x ** Bool, var.x.subtype(Ord)
cct.eq = var.x ** var.x ** Bool, var.x.subtype(Val)
cct.conj = Bool ** Bool ** Bool
cct.notj = Bool ** Bool
#compose2 notj conj
cct.disj = Bool ** Bool ** Bool  # define as not-conjunction

# aggregations of collections
cct.count = R1(Obj) ** Ratio
cct.size = R1(Loc) ** Ratio
#define: relunion (regions x)
cct.merge = R1(Reg) ** Reg
cct.centroid = R1(Loc) ** Loc
cct.name = R1(Nom) ** Nom

# statistical operations
cct.avg = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Itv)
cct.min = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ord)
cct.max = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ord)
cct.sum = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ratio)
# define in terms of: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
cct.contentsum = R2(Reg, var.x) ** R2(Reg, var.x), var.x.subtype(Ratio)
# define in terms of: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
cct.coveragesum = R2(var.v, var.x) ** R2(Nom, var.x), var.x.subtype(Ratio), var.v.subtype(Nom)


##########################################################################
# Geometric transformations
cct.interpol = R2(Reg, var.x) ** R1(Loc) ** R2(Loc, var.x), var.x.subtype(Itv)
# define in terms of ldist: join_with1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
cct.extrapol = R2(Obj, Reg) ** R2(Loc, Bool)  # Buffering, define in terms of Dist
cct.arealinterpol = R2(Reg, var.x) ** R1(Reg) ** R2(Reg, var.x), var.x.subtype(Ratio)
cct.slope = R2(Loc, var.x) ** R2(Loc, Ratio), var.x.subtype(Itv)
cct.aspect = R2(Loc, var.x) ** R2(Loc, Ratio), var.x.subtype(Itv)

# deify/reify, nest/get, invert/revert might be defined in terms of inverse
#cct.inverse = (var.x ** var.y) ** (var.y ** R1(var.x))

# conversions
cct.reify = R1(Loc) ** Reg
cct.deify = Reg ** R1(Loc)
cct.nest = var.x ** R1(var.x)  # Puts values into some unary relation
cct.nest2 = var.x ** var.y ** R2(var.x, var.y)
cct.nest3 = var.x ** var.y ** var.z ** R3(var.x, var.y, var.z)
cct.get = R1(var.x) ** var.x, var.x.subtype(Val)
#define: groupby reify (nomfield x)
cct.invert = R2(Loc, var.x) ** R2(var.x, Reg), var.x.subtype(Qlt)
#define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
cct.revert = R2(var.x, Reg) ** R2(Loc, var.x), var.x.subtype(Qlt)
#define?
# join_with2 nest (get_attrL (objectregionratios x)) (get_attrR (objectregionratios x))
# groupbyR id (join_key (select eq (rTopo (pi2 (get_attrL (objectregionratios x))) (pi2 (get_attrL (objectregionratios x)))) in) (get_attrR (objectregionratios x)))
cct.getamounts = R3a(Obj, Reg, var.x) ** R2(Reg, var.x), var.x.subtype(Ratio)

# operators on quantified relations
# define odist in terms of the minimal ldist
cct.oDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
cct.lDist = R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
# similar for lodist
cct.loDist = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj)
cct.oTopo = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj)
cct.loTopo = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj)
# otopo can be defined in terms of rtopo? in rtopo, if points of a region are
# all inside, then the region is inside
cct.rTopo = R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg)
cct.lTopo = R1(Loc) ** Reg ** R3(Loc, Nom, Reg)
cct.lrTopo = R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg)
cct.nDist = R1(Obj) ** R1(Obj) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj)
cct.lVis = R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)

# amount operations
cct.fcont = (R2(var.v, var.x) ** var.y) ** R2(Loc, var.x) ** Reg ** var.y, var.x.subtype(Qlt), var.y.subtype(Qlt), var.v.subtype(Val)
cct.ocont = R2(Obj, Reg) ** Reg ** Count
cct.fcover = R2(Loc, var.x) ** R1(var.x) ** Reg, var.x.subtype(Qlt)
cct.ocover = R2(Obj, Reg) ** R1(Obj) ** Reg


###########################################################################
# Relational transformations

#cct.apply = R2(var.x, var.y) ** var.x ** var.y

#Set union and set difference
#define nest ()
cct.set_union = (
    var.rel ** var.rel ** var.rel
)
cct.set_diff = (
    var.rel ** var.rel ** var.rel
)
cct.relunion= (
    R1(var.rel)  ** var.rel
)

# functions to handle multiple attributes of the same types with 1 key
cct.join_attr = R2(var.x, var.y) ** R2(var.x, var.z) ** R3a(var.x, var.y, var.z)
cct.get_attrL = R3a(var.x, var.y, var.z) ** R2(var.x, var.y)
cct.get_attrR = R3a(var.x, var.y, var.z) ** R2(var.x, var.z)

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

# Join of two unary concepts, like a table join.
# is join the same as join_with2 eq?
cct.join = R2(var.x, var.y) ** R2(var.y, var.z) ** R2(var.x, var.z)

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
cct.join_with1 = (
    (var.x11 ** var.x2)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2),
    var.x1.subtype(var.x11)
)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
cct.join_with2 = (
    (var.x11 ** var.x22 ** var.x3)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2) ** R2(var.y, var.x3),
    var.x1.subtype(var.x11), var.x2.subtype(var.x22)
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

#Group by qualities of unary concepts
cct.groupby = (
    (R1(var.x) ** var.q) ** R2(var.x, var.y) ** R2(var.y, var.q)
)
