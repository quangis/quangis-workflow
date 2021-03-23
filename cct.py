"""
Module containing the core concept transformation algebra. Usage:

    >>> from cct import algebra
    >>> expr = algebra.parse("pi1 (objects data)")
    >>> print(expr)
    R(Obj)
"""

from transformation_algebra.type import Operator, Schema, operators, _
from transformation_algebra.expr import TransformationAlgebra


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
objectnominals = R2(Obj, Nom)
objectcounts = R2(Obj, Count)

pointmeasures = R2(Reg, Itv)
amountpatches = R2(Reg, Nom)
countamounts = R2(Reg, Count)
boolcoverages = R2(Bool, Reg)
boolratio = R2(Bool, Ratio)
nomcoverages = R2(Nom, Reg)
nomsize = R2(Nom, Ratio)
contour = R2(Ord, Reg)
contourline = R2(Itv, Reg)
objectregions = R2(Obj, Reg)
objectratios = R2(Obj, Ratio)
objectregionratios = R3a(Obj, Reg, Ratio)
objectregionnominals = R3a(Obj, Reg, Nom)
objectregioncounts = R3a(Obj, Reg, Count)
objectregionattr = Schema(lambda x: R3a(Obj, Reg, x))
field = R2(Loc, Ratio)
nomfield = R2(Loc, Nom)
boolfield = R2(Loc, Bool)
ordfield = R2(Loc, Ord)
itvfield = R2(Loc, Itv)
ratiofield = R2(Loc, Ratio)
object = Obj
objects = R1(Obj)
region = Reg
regions = R1(Reg)
locs = R1(Loc)
in_ = Nom
contains = Nom
out = Nom
noms = R1(Nom)
ratios = R1(Ratio)
countV = Count
ratioV = Ratio
interval = Itv
ordinal = Ord
nominal = Nom
true = Bool
rationetwork = R3(Obj, Ratio, Obj)

###########################################################################
# Math/stats transformations


# Derivations

# primitive
ratio = Ratio ** Ratio ** Ratio
# primitive
product = Ratio ** Ratio ** Ratio
# primitive
leq = Ord ** Ord ** Bool
# primitive
eq = Val ** Val ** Bool
# primitive
conj = Bool ** Bool ** Bool
# primitive
notj = Bool ** Bool
# define: compose2 notj conj
disj = Bool ** Bool ** Bool  # define as not-conjunction


# Aggregations of collections

# primitive
count = R1(Obj) ** Ratio
# primitive
size = R1(Loc) ** Ratio
# define: relunion (regions x)
merge = R1(Reg) ** Reg
# primitive
centroid = R1(Loc) ** Loc
# primitive
name = R1(Nom) ** Nom


# Statistical operations

# primitive
avg = R2(Val, Itv) ** Itv
# primitive
min = R2(Val, Ord) ** Ord
# primitive
max = R2(Val, Ord) ** Ord
# primitive
sum = R2(Val, Ratio) ** Ratio
# define: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
contentsum = R2(Reg, Ratio) ** R2(Reg, Ratio)
# define: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
coveragesum = R2(Nom, Ratio) ** R2(Nom, Ratio)


##########################################################################
# Geometric transformations

# primitive
interpol = R2(Reg, Itv) ** R1(Loc) ** R2(Loc, Itv)
# define: apply1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
extrapol = R2(Obj, Reg) ** R2(Loc, Bool)  # Buffering, define in terms of Dist
# primitive
arealinterpol = R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio)
# primitive
slope = R2(Loc, Itv) ** R2(Loc, Ratio)
# primitive
aspect = R2(Loc, Itv) ** R2(Loc, Ratio)
#primitive
flowdirgraph = R2(Loc, Itv) ** R3(Loc, Bool, Loc) #generates a relational field based on main flow direction from a DEM
#primitive
accumulate = R3(Loc, Bool, Loc) ** R2(Loc, R1(Loc)) #accumulates a relational field in terms of its coverage (upstream)


# Conversions

# primitive
reify = R1(Loc) ** Reg
# primitive
deify = Reg ** R1(Loc)
#primitive: Interpet a name as an object
objectify = Nom ** Obj
# primitive
nest = Schema(lambda x: x ** R1(x))  # Puts values into some unary relation
# primitive
nest2 = Schema(lambda x, y: x ** y ** R2(x, y))
# primitive
nest3 = Schema(lambda x, y, z: x ** y ** z ** R3(x, y, z))
# primitive
add = Schema(lambda x: R1(x) ** x ** R1(x))
# primitive
get = Schema(lambda x: R1(x) ** x | x @ Val)
# define: groupby reify (nomfield x)
invert = Schema(lambda x: R2(Loc, x) ** R2(x, Reg) | x @ Qlt)
# define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
revert = Schema(lambda x: R2(x, Reg) ** R2(Loc, x) | x @ Qlt)
# define: join (groupby get (get_attrL (objectregionratios x1))) (get_attrR (objectregionratios x1))
getamounts = Schema(lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | x @ Ratio)


# Operators on quantified relations

# primitive
lDist = R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
# define: prod3 (apply1 (compose (groupbyL min) (lDist (locs x1))) (apply1 deify (objectregions x2)))
loDist = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj)
# define: prod3 (apply1 (compose (groupbyR min) ((swap loDist) (objectregions x1))) (apply1 deify (objectregions x2)))
oDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)

# primitive
lTopo = R1(Loc) ** Reg ** R3(Loc, Nom, Reg)
# define: prod3 (apply1 (compose (groupbyL id) (lTopo (locs x1))) (objectregions x2))
loTopo = R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj)
# define: prod3 (apply1 (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) (apply1 deify (objectregions x2)))
oTopo = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj)
# define: prod3 (apply (compose (groupbyL id) (lTopo (locs x1))) (regions x2))
lrTopo = R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg)
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap lrTopo) (regions x1))) deify) (regions x2))
rTopo = R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg)
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) deify) (regions x2))
orTopo = R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg)

# primitive
# build network
nbuild = R3a(Obj, Reg, Ratio) ** R3(Obj, Ratio, Obj)
nDist = R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj)
lVis = R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)


# Amount operations

# define: sum (join_subset (field x2) (deify (region x3)))
fcont = Schema(lambda v, x, y:
    (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | x @ Qlt | y @ Qlt)
# define: get (pi2 (groupbyR count (select eq (orTopo (objectregions x1) (nest (region x2))) in)))
ocont = R2(Obj, Reg) ** Reg ** Count
# define: reify (pi1 (join_subset (field x1) (ratios x2)))
fcover = Schema(lambda x:
    R2(Loc, x) ** R1(x) ** Reg | x @ Qlt)
# define: merge (pi2 (join_subset (objectregions x1) (objects x2)))
ocover = R2(Obj, Reg) ** R1(Obj) ** Reg

###########################################################################
# Functional and Relational transformations


# Functional

# primitive
compose = Schema(lambda α, β, γ:
    (β ** γ) ** (α ** β) ** (α ** γ)
)

# primitive
compose2 = Schema(lambda α, β, γ, δ:
    (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ)
)

# primitive
swap = Schema(lambda α, β, γ:
    (α ** β ** γ) ** (β ** α ** γ)
)

# primitive
id = Schema(lambda α: α ** α)

# primitive
apply = Schema(lambda x, y:
    (x ** y) ** R1(x) ** R2(x, y)
)


# Set union and set difference

# define: relunion (add (nest (regions x)) (regions y))
set_union = Schema(lambda rel:
    rel ** rel ** rel
)

# primitive
set_diff = Schema(lambda rel:
    rel ** rel ** rel
)

# define: set_diff rel1 (set_diff rel1 rel2)
set_inters = Schema(lambda rel:
    rel ** rel ** rel
)
# primitive
relunion = Schema(lambda rel:
    R1(rel) ** rel
)

# A constructor for quantified relations. prod generates a cartesian product as
# a nested binary relation. prod3 generates a quantified relation from two
# nested binary relations. The keys of the nested relations become two keys of
# the quantified relation.
# define: apply1 (compose ((swap apply1) (objectratios x2)) ratio) (ratiofield x1)
prod = Schema(lambda x, y, z, u, w:
    (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u))
)

# primitive
prod3 = Schema(lambda x, y, z:
    R2(z, R2(x, y)) ** R3(x, y, z)
)

# Projection (π). Projects a given relation to one of its attributes, resulting
# in a collection. Projection is also possible for multiple attributes.

# primitive
pi1 = Schema(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=1))
# primitive
pi2 = Schema(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=2))
# primitive
pi3 = Schema(lambda x: R3(_, _, x) ** R1(x))
# primitive
pi12 = Schema(lambda x, y: R3(x, y, _) ** R2(x, y))
# primitive
pi23 = Schema(lambda x, y: R3(_, x, y) ** R2(x, y))


# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.

# primitive
select = Schema(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** y ** rel
    | rel @ operators(R1, R2, R3, param=x))

# primitive
select2 = Schema(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** rel
    | rel @ operators(R1, R2, R3, param=x)
    | rel @ operators(R1, R2, R3, param=y)
)


# Join of two unary concepts, like a table join.
# primitive
join = Schema(lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z))

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
# primitive
join_subset = Schema(lambda x, rel:
    rel ** R1(x) ** rel
    | rel @ operators(R1, R2, R3, R3a, param=x))

# functions to handle multiple attributes (with 1 key)
# define: prod3 (pi12 (select2 eq (prod3 (apply1 (compose ((swap apply1) (boolfield x1)) nest2) (ratiofield x2)))))
join_attr = Schema(lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z))
get_attrL = Schema(lambda x, y, z: R3a(x, y, z) ** R2(x, y))
get_attrR = Schema(lambda x, y, z: R3a(x, y, z) ** R2(x, z))


# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
# define: prod3 (apply1 (join_subset (objectregions x2)) (groupbyL pi1 (rationetwork x1)))
join_key = Schema(lambda x, q1, y, rel, q2:
    R3(x, q1, y) ** rel ** R3(x, q2, y)
    | rel @ [R2(x, q2), R2(y, q2)])


# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa/join_with1.
# define: join (objectregions x) (apply id (pi2 (objectregions x)))
apply1 = Schema(lambda x1, x2, y:
    (x1 ** x2) ** R2(y, x1) ** R2(y, x2))


# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio/join_with2 and others.
# define: pi12 (select2 eq (prod3 (prod conj (boolfield x1) (boolfield x2))))
apply2 = Schema(lambda x1, x2, x3, y:
    (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3))


# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.

# primitive
groupbyL = Schema(lambda rel, l, q1, q2, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(l, q2)
    | rel @ [R1(r), R2(r, q1)])

# primitive
groupbyR = Schema(lambda rel, q2, l, q1, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(r, q2)
    | rel @ [R1(l), R2(l, q1)])

# Group by qualities of binary relations
# example:  groupby count (objectregions x)
# primitive
groupby = Schema(lambda l, q, y:
    (R1(l) ** q) ** R2(l, y) ** R2(y, q))


##############################################################################
# Generate an algebra out of all signatures defined in this module
algebra = TransformationAlgebra.from_dict(globals())
