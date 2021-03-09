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
cct.objectratios = R2(Obj, Ratio), 1
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
cct.regions = R1(Reg), 1
cct.locs = R1(Loc), 1
cct.in_ = Nom, 0
cct.contains = Nom, 0
cct.out = Nom, 0
cct.noms = R1(Nom), 1
cct.ratios = R1(Ratio), 1
cct.countV = Count, 1
cct.ratioV = Ratio, 1
cct.interval = Itv, 1
cct.ordinal = Ord, 1
cct.nominal = Nom, 1
cct.true = Bool, 0
cct.rationetwork = R3(Obj, Ratio, Obj), 1

###########################################################################
# Math/stats transformations

# derivations
# primitive
cct.ratio = Ratio ** Ratio ** Ratio
# primitive
cct.product = Ratio ** Ratio ** Ratio
# primitive
cct.leq = var.x ** var.x ** Bool, var.x.subtype(Ord)
# primitive
cct.eq = var.x ** var.x ** Bool, var.x.subtype(Val)
# primitive
cct.conj = Bool ** Bool ** Bool
# primitive
cct.notj = Bool ** Bool
#define: compose2 notj conj
cct.disj = Bool ** Bool ** Bool  # define as not-conjunction

# aggregations of collections
# primitive
cct.count = R1(Obj) ** Ratio
# primitive
cct.size = R1(Loc) ** Ratio
#define: relunion (regions x)
cct.merge = R1(Reg) ** Reg
# primitive
cct.centroid = R1(Loc) ** Loc
# primitive
cct.name = R1(Nom) ** Nom

# statistical operations
# primitive
cct.avg = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Itv)
# primitive
cct.min = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ord)
# primitive
cct.max = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ord)
# primitive
cct.sum = R2(var.v, var.x) ** var.x, var.v.subtype(Val), var.x.subtype(Ratio)
# define: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
cct.contentsum = R2(Reg, var.x) ** R2(Reg, var.x), var.x.subtype(Ratio)
# define: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
cct.coveragesum = R2(var.v, var.x) ** R2(Nom, var.x), var.x.subtype(Ratio), var.v.subtype(Nom)


##########################################################################
# Geometric transformations
# primitive
cct.interpol = R2(Reg, var.x) ** R1(Loc) ** R2(Loc, var.x), var.x.subtype(Itv)
# define: apply1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
cct.extrapol = R2(Obj, Reg) ** R2(Loc, Bool)  # Buffering, define in terms of Dist
# primitive
cct.arealinterpol = R2(Reg, var.x) ** R1(Reg) ** R2(Reg, var.x), var.x.subtype(Ratio)
# primitive
cct.slope = R2(Loc, var.x) ** R2(Loc, Ratio), var.x.subtype(Itv)
# primitive
cct.aspect = R2(Loc, var.x) ** R2(Loc, Ratio), var.x.subtype(Itv)

# deify/reify, nest/get, invert/revert might be defined in terms of inverse
#cct.inverse = (var.x ** var.y) ** (var.y ** R1(var.x))

# conversions
# primitive
cct.reify = R1(Loc) ** Reg
# primitive
cct.deify = Reg ** R1(Loc)
# primitive: interpret name as object
cct.objectify = Nom ** Obj
# primitive
cct.nest = var.x ** R1(var.x)  # Puts values into some unary relation
# primitive
cct.nest2 = var.x ** var.y ** R2(var.x, var.y)
# primitive
cct.nest3 = var.x ** var.y ** var.z ** R3(var.x, var.y, var.z)
# primitive
cct.add = R1(var.x) ** var.x ** R1(var.x)
# primitive
cct.get = R1(var.x) ** var.x, var.x.subtype(Val)
#define: groupby reify (nomfield x)
cct.invert = R2(Loc, var.x) ** R2(var.x, Reg), var.x.subtype(Qlt)
#define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
cct.revert = R2(var.x, Reg) ** R2(Loc, var.x), var.x.subtype(Qlt)
#define: join (groupby get (get_attrL (objectregionratios x1))) (get_attrR (objectregionratios x1))
cct.getamounts = R3a(Obj, Reg, var.x) ** R2(Reg, var.x), var.x.subtype(Ratio)

# operators on quantified relations
#
# primitive
cct.lDist = R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
# define: prod3 (apply1 (compose (groupbyL min) (lDist (locs x1))) (apply1 deify (objectregions x2)))
cct.loDist = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj)
# define: prod3 (apply1 (compose (groupbyR min) ((swap loDist) (objectregions x1))) (apply1 deify (objectregions x2)))
cct.oDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
#
# primitive
cct.lTopo = R1(Loc) ** Reg ** R3(Loc, Nom, Reg)
#define: prod3 (apply1 (compose (groupbyL id) (lTopo (locs x1))) (objectregions x2))
cct.loTopo = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj)
#define: prod3 (apply1 (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) (apply1 deify (objectregions x2)))
cct.oTopo = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj)
# define: prod3 (apply (compose (groupbyL id) (lTopo (locs x1))) (regions x2))
cct.lrTopo = R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg)
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap lrTopo) (regions x1))) deify) (regions x2))
cct.rTopo = R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg)
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) deify) (regions x2))
cct.orTopo = R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg)

# primitive
cct.nDist = R1(Obj) ** R1(Obj) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj)
cct.lVis = R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)

# amount operations
# define: sum (join_subset (field x2) (deify (region x3)))
cct.fcont = (R2(var.v, var.x) ** var.y) ** R2(Loc, var.x) ** Reg ** var.y, var.x.subtype(Qlt), var.y.subtype(Qlt), var.v.subtype(Val)
# define: get (pi2 (groupbyR count (select eq (orTopo (objectregions x1) (nest (region x2))) in)))
cct.ocont = R2(Obj, Reg) ** Reg ** Count
# define: reify (pi1 (join_subset (field x1) (ratios x2)))
cct.fcover = R2(Loc, var.x) ** R1(var.x) ** Reg, var.x.subtype(Qlt)
# define: merge (pi2 (join_subset (objectregions x1) (objects x2)))
cct.ocover = R2(Obj, Reg) ** R1(Obj) ** Reg


###########################################################################
# Functional and Relational transformations

#Functional
# primitive
cct.compose = (var.y ** var.z) ** (var.x ** var.y) ** (var.x ** var.z)
# primitive
cct.compose2 = (var.y ** var.z) ** (var.w ** var.x ** var.y) ** (var.w ** var.x ** var.z)
# primitive
cct.swap = (var.x ** var.y ** var.z) ** (var.y ** var.x ** var.z)
# primitive
cct.id = var.x ** var.x
# primitive
cct.apply = (var.x11 ** var.y) **  R1(var.x1)  ** R2(var.x1, var.y), var.x1.subtype(var.x11)

#Set union and set difference
#define: relunion (add (nest (regions x)) (regions y))
cct.set_union = (
    var.rel ** var.rel ** var.rel
)
# primitive
cct.set_diff = (
    var.rel ** var.rel ** var.rel
)
#define: set_diff rel1 (set_diff rel1 rel2)
cct.set_inters = (
    var.rel ** var.rel ** var.rel
)
# primitive
cct.relunion= (
    R1(var.rel) ** var.rel
)

#A constructor for quantified relations. prod generates a cartesian product as a nested binary relation. prod3 generates a quantified relation from two nested binary relations. The keys of the nested relations become two keys of the quantified relation.
#define: apply1 (compose ((swap apply1) (objectratios x2)) ratio) (ratiofield x1)
cct.prod = (var.y ** var.z ** var.u) ** R2(var.x, var.y) ** R2(var.w, var.z) ** R2(var.x, R2(var.w, var.u))
# primitive
cct.prod3 = (
    R2(var.z, R2(var.x, var.y)) ** R3(var.x, var.y, var.z)
)

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection. Projection is also possible for multiple attributes
# primitive
cct.pi1 = var.rel ** R1(var.x), var.rel.param(var.x, at=1)
# primitive
cct.pi2 = var.rel ** R1(var.x), var.rel.param(var.x, at=2)
# primitive
cct.pi3 = var.rel ** R1(var.x), var.rel.param(var.x, at=3)
# primitive
cct.pi12 = R3(var.x, var.y, var.z) ** R2(var.x, var.y)
# primitive
cct.pi23 = R3(var.z, var.x, var.y) ** R2(var.x, var.y)

# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.
# primitive
cct.select = (
    (var.x ** var.y ** Bool) ** var.rel ** var.y ** var.rel,
    var.rel.param(var.x, subtype=True)
)
# primitive
cct.select2 = (
    (var.x ** var.y ** Bool) ** var.rel ** var.rel,
    var.rel.param(var.x, subtype=True), var.rel.param(var.y, subtype=True)
)

# Join of two unary concepts, like a table join.#
# primitive
cct.join = R2(var.x, var.y) ** R2(var.y, var.z) ** R2(var.x, var.z)

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
# primitive
cct.join_subset = (
    var.rel ** R1(var.x) ** var.rel,
    var.rel.param(var.x)
)

# functions to handle multiple attributes (with 1 key)
# define: prod3 (pi12 (select2 eq (prod3 (apply1 (compose ((swap apply1) (boolfield x1)) nest2) (ratiofield x2)))))
cct.join_attr = R2(var.x, var.y) ** R2(var.x, var.z) ** R3a(var.x, var.y, var.z)
cct.get_attrL = R3a(var.x, var.y, var.z) ** R2(var.x, var.y)
cct.get_attrR = R3a(var.x, var.y, var.z) ** R2(var.x, var.z)

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
# define: prod3 (apply1 (join_subset (objectregions x2)) (groupbyL pi1 (rationetwork x1)))
cct.join_key = (
    R3(var.x, var.q1, var.y) ** var.rel ** R3(var.x, var.q2, var.y),
    var.rel.member(R2(var.x, var.q2), R2(var.y, var.q2))
)

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa.
# define: join (objectregions x) (apply id (pi2 (objectregions x)))
cct.apply1 = (
    (var.x11 ** var.x2)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2),
    var.x1.subtype(var.x11)
)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
# define: pi12 (select2 eq (prod3 (prod conj (boolfield x1) (boolfield x2))))
cct.apply2 = (
    (var.x11 ** var.x22 ** var.x3)
    ** R2(var.y, var.x1) ** R2(var.y, var.x2) ** R2(var.y, var.x3),
    var.x1.subtype(var.x11), var.x2.subtype(var.x22)
)


# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
# primitive
cct.groupbyL = (
    (var.rel ** var.q2) ** R3(var.l, var.q1, var.r) ** R2(var.l, var.q2),
    var.rel.member(R1(var.r), R2(var.r, var.q1))
)
# primitive
cct.groupbyR = (
    (var.rel ** var.q2) ** R3(var.l, var.q1, var.r) ** R2(var.r, var.q2),
    var.rel.member(R1(var.l), R2(var.l, var.q1))
)

#Group by qualities of binary relations
# example:  groupby count (objectregions x)
# primitive
cct.groupby = (
    (R1(var.l) ** var.q) ** R2(var.l, var.y) ** R2(var.y, var.q)
)
