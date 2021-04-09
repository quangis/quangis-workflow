"""
Module containing the core concept transformation algebra. Usage:

    >>> from cct import cct
    >>> cct.parse("pi1 (objects data)")
    R1(Obj)
     ├─╼ pi1 : rel ** R1(x) | rel @ [R1(x), R2(x, _), R3(x, _, _)]
     └─╼ objects data : R1(Obj)
"""

from transformation_algebra import \
    Type, operators, _, TransformationAlgebra, Data, Operation


##############################################################################
# Types and type synonyms

Val = Type.declare('Val')
Obj = Type.declare('Obj', supertype=Val)  # O
Reg = Type.declare('Reg', supertype=Val)  # S
Loc = Type.declare('Loc', supertype=Val)  # L
Qlt = Type.declare('Qlt', supertype=Val)  # Q
Nom = Type.declare('Nom', supertype=Qlt)
Bool = Type.declare('Bool', supertype=Nom)
Ord = Type.declare('Ord', supertype=Nom)
Itv = Type.declare('Itv', supertype=Ord)
Ratio = Type.declare('Ratio', supertype=Itv)
Count = Type.declare('Count', supertype=Ratio)
R1 = Type.declare('R1', params=1)  # Collections
R2 = Type.declare('R2', params=2)  # Unary core concepts, 1 key (left)
R3 = Type.declare('R3', params=3)  # Quantified relation, 2 keys (l & r)
R3a = Type.declare('R3a', params=3)  # Ternary relation, 1 key (left)

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

Δ = Data

# Reintroducing these for now to make sure the tests still work
objectnominals = Δ(R2(Obj, Nom))
objectcounts = Δ(R2(Obj, Count))

pointmeasures = Δ(R2(Reg, Itv))
amountpatches = Δ(R2(Reg, Nom))
countamounts = Δ(R2(Reg, Count))
boolcoverages = Δ(R2(Bool, Reg))
boolratio = Δ(R2(Bool, Ratio))
nomcoverages = Δ(R2(Nom, Reg))
nomsize = Δ(R2(Nom, Ratio))
contour = Δ(R2(Ord, Reg))
contourline = Δ(R2(Itv, Reg))
objectregions = Δ(R2(Obj, Reg))
objectratios = Δ(R2(Obj, Ratio))
objectregionratios = Δ(R3a(Obj, Reg, Ratio))
objectregionnominals = Δ(R3a(Obj, Reg, Nom))
objectregioncounts = Δ(R3a(Obj, Reg, Count))
objectregionattr = Δ(lambda x: R3a(Obj, Reg, x))
field = Δ(R2(Loc, Ratio))
nomfield = Δ(R2(Loc, Nom))
boolfield = Δ(R2(Loc, Bool))
ordfield = Δ(R2(Loc, Ord))
itvfield = Δ(R2(Loc, Itv))
ratiofield = Δ(R2(Loc, Ratio))
locationfield = Δ(R2(Loc, Loc))
object = Δ(Obj)
objects = Δ(R1(Obj))
region = Δ(Reg)
regions = Δ(R1(Reg))
locs = Δ(R1(Loc))
in_ = Δ(Nom)
contains = Δ(Nom)
out = Δ(Nom)
noms = Δ(R1(Nom))
ratios = Δ(R1(Ratio))
countV = Δ(Count)
ratioV = Δ(Ratio)
interval = Δ(Itv)
ordinal = Δ(Ord)
nominal = Δ(Nom)
true = Δ(Bool)
rationetwork = Δ(R3(Obj, Ratio, Obj))

###########################################################################
# Math/stats transformations

Ω = Operation

# Derivations

# primitive
ratio = Ω(Ratio ** Ratio ** Ratio)
# primitive
product = Ω(Ratio ** Ratio ** Ratio)
# primitive
leq = Ω(Ord ** Ord ** Bool)
# primitive
eq = Ω(Val ** Val ** Bool)
# primitive
conj = Ω(Bool ** Bool ** Bool)
# primitive
notj = Ω(Bool ** Bool)
# define: compose2 notj conj
disj = Ω(Bool ** Bool ** Bool)  # define as not-conjunction


# Aggregations of collections

# primitive
count = Ω(R1(Obj) ** Ratio)
# primitive
size = Ω(R1(Loc) ** Ratio)
# define: relunion (regions x)
merge = Ω(R1(Reg) ** Reg)
# primitive
centroid = Ω(R1(Loc) ** Loc)
# primitive
name = Ω(R1(Nom) ** Nom)


# Statistical operations

# primitive
avg = Ω(R2(Val, Itv) ** Itv)
# primitive
min = Ω(R2(Val, Ord) ** Ord)
# primitive
max = Ω(R2(Val, Ord) ** Ord)
# primitive
sum = Ω(R2(Val, Ratio) ** Ratio)
# define: nest2 (merge (pi1 (countamounts x1))) (sum (countamounts x1))
contentsum = Ω(R2(Reg, Ratio) ** R2(Reg, Ratio))
# define: nest2 (name (pi1 (nomcoverages x1))) (merge (pi2(nomcoverages x1)))
coveragesum = Ω(R2(Nom, Ratio) ** R2(Nom, Ratio))


##########################################################################
# Geometric transformations

# primitive
interpol = Ω(R2(Reg, Itv) ** R1(Loc) ** R2(Loc, Itv))
# define: apply1 (leq (ratioV w))(groupbyL (min) (loDist (deify (region y)) (objectregions x)))
extrapol = Ω(R2(Obj, Reg) ** R2(Loc, Bool))  # Buffering, define in terms of Dist
# primitive
arealinterpol = Ω(R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio))
# primitive
slope = Ω(R2(Loc, Itv) ** R2(Loc, Ratio))
# primitive
aspect = Ω(R2(Loc, Itv) ** R2(Loc, Ratio))
#primitive
flowdirgraph = Ω(R2(Loc, Itv) ** R2(Loc, Loc)) #generates a location field based on main flow direction from a DEM
#primitive
accumulate = Ω(R2(Loc, Loc) ** R2(Loc, R1(Loc))) #accumulates a location field in terms of its coverage (upstream)


# Conversions

# primitive
reify = Ω(R1(Loc) ** Reg)
# primitive
deify = Ω(Reg ** R1(Loc))
#primitive: Interpet a name as an object
objectify = Ω(Nom ** Obj)
# primitive
nest = Ω(lambda x: x ** R1(x))  # Puts values into some unary relation
# primitive
nest2 = Ω(lambda x, y: x ** y ** R2(x, y))
# primitive
nest3 = Ω(lambda x, y, z: x ** y ** z ** R3(x, y, z))
# primitive
add = Ω(lambda x: R1(x) ** x ** R1(x))
# primitive
get = Ω(lambda x: R1(x) ** x | x @ Val)
# define: groupby reify (nomfield x)
invert = Ω(lambda x: R2(Loc, x) ** R2(x, Reg) | x @ Qlt)
# define: groupbyL id (join_key (select eq (lTopo (deify (merge (pi2 (nomcoverages x)))) (merge (pi2 (nomcoverages x)))) in) (groupby name (nomcoverages x)))
revert = Ω(lambda x: R2(x, Reg) ** R2(Loc, x) | x @ Qlt)
# define: join (groupby get (get_attrL (objectregionratios x1))) (get_attrR (objectregionratios x1))
getamounts = Ω(lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | x @ Ratio)


# Operators on quantified relations

# primitive
lDist = Ω(R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc))
# define: prod3 (apply1 (compose (groupbyL min) (lDist (locs x1))) (apply1 deify (objectregions x2)))
loDist = Ω(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj))
# define: prod3 (apply1 (compose (groupbyR min) ((swap loDist) (objectregions x1))) (apply1 deify (objectregions x2)))
oDist = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj))

# primitive
lTopo = Ω(R1(Loc) ** Reg ** R3(Loc, Nom, Reg))
# define: prod3 (apply1 (compose (groupbyL id) (lTopo (locs x1))) (objectregions x2))
loTopo = Ω(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj))
# define: prod3 (apply1 (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) (apply1 deify (objectregions x2)))
oTopo = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj))
# define: prod3 (apply (compose (groupbyL id) (lTopo (locs x1))) (regions x2))
lrTopo = Ω(R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg))
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap lrTopo) (regions x1))) deify) (regions x2))
rTopo = Ω(R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg))
# define: prod3 (apply (compose (compose (groupbyR (compose name pi2)) ((swap loTopo) (objectregions x1))) deify) (regions x2))
orTopo = Ω(R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg))

# primitive
# build network
nbuild = Ω(R3a(Obj, Reg, Ratio) ** R3(Obj, Ratio, Obj))
nDist = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj))
lVis = Ω(R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc))


# Amount operations

# define: sum (join_subset (field x2) (deify (region x3)))
fcont = Ω(lambda v, x, y:
    (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | x @ Qlt | y @ Qlt)
# define: get (pi2 (groupbyR count (select eq (orTopo (objectregions x1) (nest (region x2))) in)))
ocont = Ω(R2(Obj, Reg) ** Reg ** Count)
# define: reify (pi1 (join_subset (field x1) (ratios x2)))
fcover = Ω(lambda x:
    R2(Loc, x) ** R1(x) ** Reg | x @ Qlt)
# define: merge (pi2 (join_subset (objectregions x1) (objects x2)))
ocover = Ω(R2(Obj, Reg) ** R1(Obj) ** Reg)

###########################################################################
# Functional and Relational transformations


# Functional

# primitive
compose = Ω(lambda α, β, γ:
    (β ** γ) ** (α ** β) ** (α ** γ)
)

# primitive
compose2 = Ω(lambda α, β, γ, δ:
    (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ)
)

# primitive
swap = Ω(lambda α, β, γ:
    (α ** β ** γ) ** (β ** α ** γ)
)

# primitive
id = Ω(lambda α: α ** α)

# primitive
apply = Ω(lambda x, y:
    (x ** y) ** R1(x) ** R2(x, y)
)


# Set union and set difference

# define: relunion (add (nest (regions x)) (regions y))
set_union = Ω(lambda rel:
    rel ** rel ** rel
)

# primitive
set_diff = Ω(lambda rel:
    rel ** rel ** rel
)

# define: set_diff rel1 (set_diff rel1 rel2)
set_inters = Ω(lambda rel:
    rel ** rel ** rel
)
# primitive
relunion = Ω(lambda rel:
    R1(rel) ** rel
)

# A constructor for quantified relations. prod generates a cartesian product as
# a nested binary relation. prod3 generates a quantified relation from two
# nested binary relations. The keys of the nested relations become two keys of
# the quantified relation.
# define: apply1 (compose ((swap apply1) (objectratios x2)) ratio) (ratiofield x1)
prod = Ω(lambda x, y, z, u, w:
    (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u))
)

# primitive
prod3 = Ω(lambda x, y, z:
    R2(z, R2(x, y)) ** R3(x, y, z)
)

# Projection (π). Projects a given relation to one of its attributes, resulting
# in a collection. Projection is also possible for multiple attributes.

# primitive
pi1 = Ω(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=1))
# primitive
pi2 = Ω(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=2))
# primitive
pi3 = Ω(lambda x: R3(_, _, x) ** R1(x))
# primitive
pi12 = Ω(lambda x, y: R3(x, y, _) ** R2(x, y))
# primitive
pi23 = Ω(lambda x, y: R3(_, x, y) ** R2(x, y))


# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.

# primitive
select = Ω(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** y ** rel
    | rel @ operators(R1, R2, R3, param=x))

# primitive
select2 = Ω(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** rel
    | rel @ operators(R1, R2, R3, param=x)
    | rel @ operators(R1, R2, R3, param=y)
)


# Join of two unary concepts, like a table join.
# primitive
join = Ω(lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z))

# Join on subset (⨝). Subset a relation to those tuples having an attribute
# value contained in a collection. Used to be bowtie.
# primitive
join_subset = Ω(lambda x, rel:
    rel ** R1(x) ** rel
    | rel @ operators(R1, R2, R3, R3a, param=x))

# functions to handle multiple attributes (with 1 key)
# define: prod3 (pi12 (select2 eq (prod3 (apply1 (compose ((swap apply1) (boolfield x1)) nest2) (ratiofield x2)))))
join_attr = Ω(lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z))
get_attrL = Ω(lambda x, y, z: R3a(x, y, z) ** R2(x, y))
get_attrR = Ω(lambda x, y, z: R3a(x, y, z) ** R2(x, z))


# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
# define: prod3 (apply1 (join_subset (objectregions x2)) (groupbyL pi1 (rationetwork x1)))
join_key = Ω(lambda x, q1, y, rel, q2:
    R3(x, q1, y) ** rel ** R3(x, q2, y)
    | rel @ [R2(x, q2), R2(y, q2)])


# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa/join_with1.
# define: join (objectregions x) (apply id (pi2 (objectregions x)))
apply1 = Ω(lambda x1, x2, y:
    (x1 ** x2) ** R2(y, x1) ** R2(y, x2))


# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio/join_with2 and others.
# define: pi12 (select2 eq (prod3 (prod conj (boolfield x1) (boolfield x2))))
apply2 = Ω(lambda x1, x2, x3, y:
    (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3))


# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.

# primitive
groupbyL = Ω(lambda rel, l, q1, q2, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(l, q2)
    | rel @ [R1(r), R2(r, q1)])

# primitive
groupbyR = Ω(lambda rel, q2, l, q1, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(r, q2)
    | rel @ [R1(l), R2(l, q1)])

# Group by qualities of binary relations
# example:  groupby count (objectregions x)
# primitive
groupby = Ω(lambda l, q, y:
    (R1(l) ** q) ** R2(l, y) ** R2(y, q))


##############################################################################
# Generate an algebra out of all definitions in this module
cct = TransformationAlgebra(**globals())
