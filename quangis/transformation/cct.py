"""
Module containing the core concept transformation algebra. Usage:

    >>> from quangis.transformation.cct import algebra
    >>> expr = algebra.parse("pi1 (objects data)")
    >>> print(expr)
    R(Obj)
"""

from quangis.transformation.type import Σ, Operator, Subtype, Member, Param
from quangis.transformation.algebra import TransformationAlgebra


##############################################################################
# Types and type synonyms

Val = Operator('Val')
Obj = Operator('Obj', supertype=Val)  # O
Reg = Operator('Reg', supertype=Val)  # S
Loc = Operator('Loc', supertype=Val)  # L
Qlt = Operator('Qlt', supertype=Val)  # Q
Nom = Operator('Nom', supertype=Qlt)
Bool = Operator('Bool', supertype=Nom)
Ord = Operator('Ord', supertype=Nom)
Itv = Operator('Itv', supertype=Ord)
Ratio = Operator('Ratio', supertype=Itv)
Count = Operator('Count', supertype=Ratio)
R1 = Operator('R1', 1)  # Collections
R2 = Operator('R2', 2)  # Unary core concepts, 1 key (left)
R3 = Operator('R3', 3)  # Quantified relation, 2 keys (l & r)
R3a = Operator('R3a', 3)  # Ternary relation, 1 key (left)

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

# Reintroducing these for now to make sure the tests still work
objectratios = Σ(R2(Obj, Ratio)), 1
objectnominals = Σ(R2(Obj, Nom)), 1
objectregions = Σ(R2(Obj, Reg)), 1
objectcounts = Σ(R2(Obj, Count)), 1

pointmeasures = Σ(R2(Reg, Itv)), 1
amountpatches = Σ(R2(Reg, Nom)), 1
countamounts = Σ(R2(Reg, Count)), 1
boolcoverages = Σ(R2(Bool, Reg)), 1
boolratio = Σ(R2(Bool, Ratio)), 1
nomcoverages = Σ(R2(Nom, Reg)), 1
nomsize = Σ(R2(Nom, Ratio)), 1
regions = Σ(R1(Reg)), 1
contour = Σ(R2(Ord, Reg)), 1
contourline = Σ(R2(Itv, Reg)), 1
objectregions = Σ(R2(Obj, Reg)), 1
objectregionratios = Σ(R3a(Obj, Reg, Ratio)), 1
objectregionnominals = Σ(R3a(Obj, Reg, Nom)), 1
objectregioncounts = Σ(R3a(Obj, Reg, Count)), 1
objectregionattr = Σ(lambda x: R3a(Obj, Reg, x)), 1
field = Σ(R2(Loc, Ratio)), 1
nomfield = Σ(R2(Loc, Nom)), 1
boolfield = Σ(R2(Loc, Bool)), 1
ordfield = Σ(R2(Loc, Ord)), 1
itvfield = Σ(R2(Loc, Itv)), 1
ratiofield = Σ(R2(Loc, Ratio)), 1
object = Σ(Obj), 1
objects = Σ(R1(Obj)), 1
region = Σ(Reg), 1
in_ = Σ(Nom), 0
out = Σ(Nom), 0
noms = Σ(R1(Nom)), 1
ratios = Σ(R1(Ratio)), 1
countV = Σ(Count), 1
ratioV = Σ(Ratio), 1
interval = Σ(Itv), 1
ordinal = Σ(Ord), 1
nominal = Σ(Nom), 1
true = Σ(Bool), 0

###########################################################################
# Math/stats transformations

# functional
compose = Σ(lambda α, β, γ: (β ** γ) ** (α ** β) ** (α ** γ))
compose2 = Σ(lambda α, β, γ, δ: (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ))
swap = Σ(lambda α, β, γ: (α ** β ** γ) ** (β ** α ** γ))
id = Σ(lambda α: α ** α)

# derivations
ratio = Σ(Ratio ** Ratio ** Ratio)
product = Σ(Ratio ** Ratio ** Ratio)
leq = Σ(lambda α: α ** α ** Bool | Subtype(α, Ord))
eq = Σ(lambda α: α ** α ** Bool | Subtype(α, Val))
conj = Σ(Bool ** Bool ** Bool)
notj = Σ(Bool ** Bool)
# compose2 notj conj
disj = Σ(Bool ** Bool ** Bool)  # define as not-conjunction

# aggregations of collections
count = Σ(R1(Obj) ** Ratio)
size = Σ(R1(Loc) ** Ratio)
# define: relunion (regions x)
merge = Σ(R1(Reg) ** Reg)
centroid = Σ(R1(Loc) ** Loc)
name = Σ(R1(Nom) ** Nom)

# statistical operations
avg = Σ(R2(Val, Itv) ** Itv)
min = Σ(R2(Val, Ord) ** Ord)
max = Σ(R2(Val, Ord) ** Ord)
sum = Σ(R2(Val, Ratio) ** Ratio)

# define in terms of: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
contentsum = Σ(lambda x: R2(Reg, x) ** R2(Reg, x) | Subtype(x, Ratio))

# define in terms of: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
coveragesum = Σ(lambda x: R2(Nom, x) ** R2(Nom, x) | Subtype(x, Ratio))


##########################################################################
# Geometric transformations
interpol = Σ(lambda x: R2(Reg, x) ** R1(Loc) ** R2(Loc, x) | Subtype(x, Itv))

# define in terms of ldist: join_with1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
extrapol = Σ(R2(Obj, Reg) ** R2(Loc, Bool))  # Buffering, define in terms of Dist
arealinterpol = Σ(lambda x: R2(Reg, x) ** R1(Reg) ** R2(Reg, x) | Subtype(x, Ratio))
slope = Σ(R2(Loc, Itv) ** R2(Loc, Ratio))
aspect = Σ(R2(Loc, Itv) ** R2(Loc, Ratio))

# deify/reify, nest/get, invert/revert might be defined in terms of inverse
#cct.inverse = (var.x ** var.y) ** (var.y ** R1(var.x))

# conversions
reify = Σ(R1(Loc) ** Reg)
deify = Σ(Reg ** R1(Loc))
nest = Σ(lambda x: x ** R1(x))  # Puts values into some unary relation
nest2 = Σ(lambda x, y: x ** y ** R2(x, y))
nest3 = Σ(lambda x, y, z: x ** y ** z ** R3(x, y, z))
get = Σ(lambda x: R1(x) ** x)
#define: groupby reify (nomfield x)
invert = Σ(lambda x: R2(Loc, x) ** R2(x, Reg) | Subtype(x, Qlt))
#define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
revert = Σ(lambda x: R2(x, Reg) ** R2(Loc, x) | Subtype(x, Qlt))
#define?
# join_with2 nest (get_attrL (objectregionratios x)) (get_attrR (objectregionratios x))
# groupbyR id (join_key (select eq (rTopo (pi2 (get_attrL (objectregionratios x))) (pi2 (get_attrL (objectregionratios x)))) in) (get_attrR (objectregionratios x)))
getamounts = Σ(lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | Subtype(x, Ratio))

# operators on quantified relations
# define odist in terms of the minimal ldist
oDist = Σ(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj))
lDist = Σ(R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc))
# similar for lodist)
loDist = Σ(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj))
oTopo = Σ(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj))
loTopo = Σ(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj))
# otopo can be defined in terms of rtopo? in rtopo, if points of a region are)
# all inside, then the region is inside)
rTopo = Σ(R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg))
lTopo = Σ(R1(Loc) ** Reg ** R3(Loc, Nom, Reg))
lrTopo = Σ(R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg))
nDist = Σ(R1(Obj) ** R1(Obj) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj))
lVis = Σ(R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc))

# amount operations
fcont = Σ(lambda v, x, y: (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | [Subtype(x, Qlt), Subtype(y, Qlt)])
ocont = Σ(R2(Obj, Reg) ** Reg ** Count)
fcover = Σ(lambda x: R2(Loc, x) ** R1(x) ** Reg | Subtype(x, Qlt))
ocover = Σ(R2(Obj, Reg) ** R1(Obj) ** Reg)


###########################################################################
# Relational transformations

#cct.apply = R2(var.x, var.y) ** var.x ** var.y

#Set union and set difference
#define nest ()
set_union = Σ(
    lambda rel: rel ** rel ** rel
)
set_diff = Σ(
    lambda rel: rel ** rel ** rel
)
relunion = Σ(
    lambda rel: R1(rel) ** rel
)

# functions to handle multiple attributes of the same types with 1 key
join_attr = Σ(lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z))
get_attrL = Σ(lambda x, y, z: R3a(x, y, z) ** R2(x, y))
get_attrR = Σ(lambda x, y, z: R3a(x, y, z) ** R2(x, z))

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection.
pi1 = Σ(lambda rel, x: rel ** R1(x) | Param(rel, x, at=1))
pi2 = Σ(lambda rel, x: rel ** R1(x) | Param(rel, x, at=2))
pi3 = Σ(lambda rel, x: rel ** R1(x) | Param(rel, x, at=3))

# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.
select = Σ(lambda x, y, rel: (x ** y ** Bool) ** rel ** y ** rel | Param(var.rel, x))

# Join of two unary concepts, like a table join.
# is join the same as join_with2 eq?
join = Σ(lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z))

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
join_subset = Σ(lambda x, rel: rel ** R1(x) ** rel | Param(x))

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
join_key = Σ(lambda x, q1, y, rel, q2: R3(x, q1, y) ** rel ** R3(x, q2, y) | Member(rel, R2(x, q2), R2(y, q2)))

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa.
join_with1 = Σ(lambda x11, y, x1, x2: (x11 ** x2) ** R2(y, x1) ** R2(y, x2) | Subtype(x1, x11))

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
join_with2 = Σ(lambda x11, x22, x3, y, x1, x2: (x11 ** x22 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3) | [Subtype(x1, x11), Subtype(x2, x22)])

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
groupbyL = Σ(lambda rel, q2, l, q1, r: (rel ** q2) ** R3(l, q1, r) ** R2(l, q2) | Member(rel, R1(r), R2(r, q1)))

groupbyR = Σ(lambda rel, q2, l, q1, r: (rel ** q2) ** R3(l, q1, r) ** R2(r, q2) | Member(rel, R1(l), R2(l, q1)))

#Group by qualities of unary concepts
groupby = Σ(lambda x, q, y: (R1(x) ** q) ** R2(x, y) ** R2(y, q))

# Generate an algebra out of all signatures defined in this module
algebra = TransformationAlgebra.from_dict(dict(globals()))
