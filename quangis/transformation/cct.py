"""
Module containing the core concept transformation algebra. Usage:

    >>> from quangis.transformation.cct import algebra
    >>> expr = algebra.parse("pi1 (objects data)")
    >>> print(expr)
    R(Obj)
"""

from quangis.transformation.type import Operator, Schema, operators
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
objectratios = R2(Obj, Ratio)  # 1
objectnominals = R2(Obj, Nom)  # 1
objectcounts = R2(Obj, Count)  # 1

pointmeasures = R2(Reg, Itv)  # 1
amountpatches = R2(Reg, Nom)   # 1
countamounts = R2(Reg, Count)  # 1
boolcoverages = R2(Bool, Reg)  # 1
boolratio = R2(Bool, Ratio)  # 1
nomcoverages = R2(Nom, Reg)  # 1
nomsize = R2(Nom, Ratio)   # 1
regions = R1(Reg)  # 1
contour = R2(Ord, Reg)  # 1
contourline = R2(Itv, Reg)  # 1
objectregions = R2(Obj, Reg)  # 1
objectregionratios = R3a(Obj, Reg, Ratio)  # 1
objectregionnominals = R3a(Obj, Reg, Nom)  # 1
objectregioncounts = R3a(Obj, Reg, Count)  # 1
objectregionattr = Schema(lambda x: R3a(Obj, Reg, x))  # 1
field = R2(Loc, Ratio)  # 1
nomfield = R2(Loc, Nom)  # 1
boolfield = R2(Loc, Bool)  # 1
ordfield = R2(Loc, Ord)  # 1
itvfield = R2(Loc, Itv)  # 1
ratiofield = R2(Loc, Ratio)  # 1
object = Obj  # 1
objects = R1(Obj)  # 1
region = Reg  # 1
in_ = Nom  # 0
out = Nom  # 0
noms = R1(Nom)  # 1
ratios = R1(Ratio)  # 1
countV = Count  # 1
ratioV = Ratio  # 1
interval = Itv  # 1
ordinal = Ord  # 1
nominal = Nom  # 1
true = Bool  # 0

###########################################################################
# Math/stats transformations

# functional
compose = Schema(lambda α, β, γ:
    (β ** γ) ** (α ** β) ** (α ** γ)
)

compose2 = Schema(lambda α, β, γ, δ:
    (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ)
)

swap = Schema(lambda α, β, γ:
    (α ** β ** γ) ** (β ** α ** γ)
)

id = Schema(lambda α: α ** α)

# derivations
ratio = Ratio ** Ratio ** Ratio
product = Ratio ** Ratio ** Ratio
leq = Ord ** Ord ** Bool
eq = Val ** Val ** Bool
conj = Bool ** Bool ** Bool
notj = Bool ** Bool
# compose2 notj conj
disj = Bool ** Bool ** Bool  # define as not-conjunction

# aggregations of collections
count = R1(Obj) ** Ratio
size = R1(Loc) ** Ratio
# define: relunion (regions x
merge = R1(Reg) ** Reg
centroid = R1(Loc) ** Loc
name = R1(Nom) ** Nom

# statistical operations
avg = R2(Val, Itv) ** Itv
min = R2(Val, Ord) ** Ord
max = R2(Val, Ord) ** Ord
sum = R2(Val, Ratio) ** Ratio

# define in terms of: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
contentsum = R2(Reg, Ratio) ** R2(Reg, Ratio)

# define in terms of: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
coveragesum = R2(Nom, Ratio) ** R2(Nom, Ratio)


##########################################################################
# Geometric transformations
interpol = R2(Reg, Itv) ** R1(Loc) ** R2(Loc, Itv)

# define in terms of ldist: join_with1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
extrapol = R2(Obj, Reg) ** R2(Loc, Bool)  # Buffering, define in terms of Dist

arealinterpol = R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio)

slope = R2(Loc, Itv) ** R2(Loc, Ratio)

aspect = R2(Loc, Itv) ** R2(Loc, Ratio)

# deify/reify, nest/get, invert/revert might be defined in terms of inverse
#cct.inverse = (var.x ** var.y) ** (var.y ** R1(var.x)

# conversions
reify = R1(Loc) ** Reg
deify = Reg ** R1(Loc)
nest = Schema(lambda x: x ** R1(x))  # Puts values into some unary relation
nest2 = Schema(lambda x, y: x ** y ** R2(x, y))
nest3 = Schema(lambda x, y, z: x ** y ** z ** R3(x, y, z))
get = Schema(lambda x: R1(x) ** x)
# define: groupby reify (nomfield x)
invert = Schema(lambda x: R2(Loc, x) ** R2(x, Reg))# | x << Qlt)
# define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
revert = Schema(lambda x: R2(x, Reg) ** R2(Loc, x))# | x << Qlt)
# define?
# join_with2 nest (get_attrL (objectregionratios x)) (get_attrR (objectregionratios x))
# groupbyR id (join_key (select eq (rTopo (pi2 (get_attrL (objectregionratios x))) (pi2 (get_attrL (objectregionratios x)))) in) (get_attrR (objectregionratios x)))
getamounts = R3a(Obj, Reg, Ratio) ** R2(Reg, Ratio)
#| x << Ratio

# operators on quantified relations
# define odist in terms of the minimal ldist
oDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
lDist = R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
# similar for lodist
loDist = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj)
oTopo = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj)
loTopo = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj)
# otopo can be defined in terms of rtopo? in rtopo, if points of a region are
# all inside, then the region is inside
rTopo = R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg)
lTopo = R1(Loc) ** Reg ** R3(Loc, Nom, Reg)
lrTopo = R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg)
nDist = R1(Obj) ** R1(Obj) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj)
lVis = R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)

# amount operations
fcont = Schema(lambda v, x, y:
    (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y
    #| x << Qlt
    #| y << Qlt
)

ocont = R2(Obj, Reg) ** Reg ** Count

fcover = Schema(lambda x:
    R2(Loc, x) ** R1(x) ** Reg
    #| x << Qlt
)

ocover = R2(Obj, Reg) ** R1(Obj) ** Reg


###########################################################################
# Relational transformations

# cct.apply = R2(var.x, var.y) ** var.x ** var.y

# Set union and set difference
# define nest ()
set_union = Schema(lambda rel:
    rel ** rel ** rel
)
set_diff = Schema(lambda rel:
    rel ** rel ** rel
)
relunion = Schema(lambda rel:
    R1(rel) ** rel
)

# functions to handle multiple attributes of the same types with 1 key
join_attr = Schema(lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z))
get_attrL = Schema(lambda x, y, z: R3a(x, y, z) ** R2(x, y))
get_attrR = Schema(lambda x, y, z: R3a(x, y, z) ** R2(x, z))

# Projection (π). Projects a given relation to one of its attributes,
# resulting in a collection.
pi1 = Schema(lambda rel, x:
    rel ** R1(x) | rel @ operators(R1, R2, R3, param=x, at=1))
pi2 = Schema(lambda rel, x:
    rel ** R1(x) | rel @ operators(R1, R2, R3, param=x, at=2))
pi3 = Schema(lambda rel, x:
    rel ** R1(x) | rel @ operators(R1, R2, R3, param=x, at=3))

# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.
select = Schema(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** y ** rel
    | rel @ operators(R1, R2, R3, param=x)
)

# Join of two unary concepts, like a table join.
# is join the same as join_with2 eq?
join = Schema(lambda x, y, z:
    R2(x, y) ** R2(y, z) ** R2(x, z)
)

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
join_subset = Schema(lambda x, rel:
    rel ** R1(x) ** rel
    | rel @ operators(R1, R2, R3, param=x)
)

# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
join_key = Schema(lambda x, q1, y, rel, q2:
    R3(x, q1, y) ** rel ** R3(x, q2, y)
    | rel @ [R2(x, q2), R2(y, q2)]
)

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa.
join_with1 = Schema(lambda x11, y, x1, x2:
    (x1 ** x2) ** R2(y, x1) ** R2(y, x2)
    #| x1 << x11
)

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio and others.
join_with2 = Schema(lambda x11, x22, x3, y, x1, x2:
    (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3)
    #| x1 << x11
    #| x2 << x22
)

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.
groupbyL = Schema(lambda rel, q2, l, q1, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(l, q2)
    | rel @ [R1(r), R2(r, q1)]
)

groupbyR = Schema(lambda rel, q2, l, q1, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(r, q2)
    | rel @ [R1(l), R2(l, q1)]
)

# Group by qualities of unary concepts
groupby = Schema(lambda x, q, y:
    (R1(x) ** q) ** R2(x, y) ** R2(y, q)
)

##############################################################################
# Generate an algebra out of all signatures defined in this module
algebra = TransformationAlgebra.from_dict(dict(globals()))
