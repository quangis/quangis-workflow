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

test = Δ(
    type=lambda x: x,
    doc="This is a data input of any type, strictly for testing."
)

pointmeasures = Δ(R2(Reg, Itv))
amountpatches = Δ(R2(Reg, Nom))
countamounts = Δ(R2(Reg, Count))
ratioamounts = Δ(R2(Reg, Ratio))
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
ratio = Ω(Ratio ** Ratio ** Ratio, derived=None)
# primitive
product = Ω(Ratio ** Ratio ** Ratio, derived=None)
# primitive
leq = Ω(Ord ** Ord ** Bool, doc="less than or equal", derived=None)
# primitive
eq = Ω(Val ** Val ** Bool, doc="equal", derived=None)
# primitive
conj = Ω(Bool ** Bool ** Bool, doc="conjunction", derived=None)
# primitive
notj = Ω(Bool ** Bool, doc="logical negation", derived=None)
# define: compose2 notj conj
disj = Ω(type = Bool ** Bool ** Bool, doc="disjunction", derived=lambda x: (compose2 (notj) (conj) (x)))
# primitive
classify = Ω(type = Itv ** Ord, doc="classification table", derived=None)

# Aggregations of collections

# primitive
count = Ω(R1(Obj) ** Count, doc="count objects", derived=None)
# primitive
size = Ω(R1(Loc) ** Ratio, doc="measure size")
merge = Ω(type=R1(Reg) ** Reg,
          derived=lambda x: reify(relunion(pi2 (apply (deify) (x)))),
          doc="merge regions"
)
# primitive
centroid = Ω(type=R1(Loc) ** Loc, doc="measure centroid", derived=None)
# primitive
name = Ω(type=R1(Nom) ** Nom, doc="combine nominal values", derived=None)


#  Statistical operations

# primitive
avg = Ω(type=lambda y: R2(Val, y) ** y | y @ Itv, doc="average", derived=None)
# primitive
min = Ω(type=lambda y: R2(Val, y) ** y | y @ Ord, doc="minimum", derived=None)
# primitive
max = Ω(type=lambda y: R2(Val, y) ** y | y @ Ord, doc="maximum", derived=None)
# primitive
sum = Ω(type=lambda y: R2(Val, y) ** y | y @ Ratio, doc="summing up values", derived=None)
# define
contentsum = Ω(
    type=lambda x: R2(Reg, x) ** R2(Reg, x) | x @ Ratio,
    doc="summing up content amounts (regions and their values)",
    derived=lambda x: nest2 (merge (pi1 (x))) (sum (x))
)
# define
coveragesum = Ω(
    type = R2(Nom, Reg) ** R2(Nom, Reg),
    doc="summing up nominal coverages",
    derived=lambda x: nest2 (name (pi1 (x))) (merge (pi2 (x)))
)


##########################################################################
# Geometric transformations

# primitive
interpol = Ω(type= lambda x: R2(Reg, x) ** R1(Loc) ** R2(Loc, x) | x @ Itv, doc="spatial point interpolation", derived=None)

extrapol = Ω(
    type=R2(Obj, Reg) ** R2(Loc, Bool),
    doc="buffering, defined in terms of some distance (given as parameter)",
    derived=lambda x: apply1 (leq (ratioV), groupbyL (min, loDist (deify (region), x)))
)

# primitive
arealinterpol = Ω(
    type=R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio),
    doc="areal interpolation",
    derived=None
)
# primitive
slope = Ω(type= R2(Loc, Itv) ** R2(Loc, Ratio) , doc="areal interpolation", derived=None)
# primitive
aspect = Ω(type= R2(Loc, Itv) ** R2(Loc, Ratio), doc="spatial aspect (cardinal direction) from DEM", derived=None)
#primitive
flowdirgraph = Ω(type=R2(Loc, Itv) ** R2(Loc, Loc), doc="flow direction graph from DEM (location field)", derived=None)
#primitive
accumulate = Ω(type=R2(Loc, Loc) ** R2(Loc, R1(Loc)), doc = "finds all locations reachable from a given location", derived=None)


# Conversions

# primitive
reify = Ω(type = R1(Loc) ** Reg, doc = "make a region from locations", derived=None)
# primitive
deify = Ω(type = Reg ** R1(Loc), doc = "make locations from a region", derived=None)
#primitive
objectify = Ω(type = Nom ** Obj, doc="interpet a name as an object", derived=None)
#primitive
nominalize = Ω(type = Obj ** Nom, doc="interpet an object as a name", derived=None)
getobjectnames = Ω(type = R1(Nom) ** R2(Obj, Nom), doc="make objects from names", derived= lambda x: apply (nominalize) (pi2 (apply (objectify) (x))))


invert = Ω(lambda x: R2(Loc, x) ** R2(x, Reg) | x @ Val, doc="inverts a field, generating a coverage", derived= lambda x: groupby (reify) (x))
revert = Ω(lambda x: R2(x, Reg) ** R2(Loc, x) | x @ Val, doc="inverts a coverage to a field", derived=lambda x : groupbyL (compose (get) (pi1)) (join_key (select (eq) (lTopo (deify (merge (pi2 (x)))) (merge (pi2 (x)))) (in_)) (groupby (get) (x)))
           )
getamounts = Ω(lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | x @ Ratio, doc="gets amounts from object based amount qualities", derived=lambda x: join (groupby (get) (get_attrL (x))) (get_attrR (x)))


# Operators on quantified relations

# primitive
lDist = Ω(R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc),doc="computes Euclidean distances between locations", derived=None)
# define
loDist = Ω(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj), doc= "computes Euclidean distances between locations and objects", derived = lambda x, y: prod3 (apply1 (compose (groupbyL (min)) (lDist (x))) (apply1 (deify) (y))))
# define
oDist = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj), doc="computes Euclidean distances between objects", derived=lambda x, y: prod3 (apply1 (compose (groupbyR (min)) ((swap (loDist)) (x))) (apply1 (deify) (y))))

# primitive
lTopo = Ω(R1(Loc) ** Reg ** R3(Loc, Nom, Reg), doc="detects the topological position of locations on a region (in, out, boundary)", derived=None)
# define
loTopo = Ω(R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj), doc="detects the topological position of locations on objects (in, out, boundary)", derived=lambda x,y: prod3 (apply1 (compose (groupbyL (compose (get) (pi2))) (lTopo ((x)))) (y))
           )

# define
oTopo = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj), doc="detects the topological relations between two sets of objects", derived= lambda x, y: prod3 (apply1 (compose (groupbyR (compose (name) (pi2))) ((swap (loTopo)) (x))) (apply1 (deify) (y))))
# define
lrTopo = Ω(R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg),doc="detects the topological position of locations on regions (in, out, boundary)", derived =lambda x,y: prod3 (apply (compose (groupbyL (compose (get) (pi2))) (lTopo ((x)))) (y))
 )
# define
rTopo = Ω(R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg), doc="detects the topological relations between two sets of regions", derived= lambda x,y: prod3 (apply (compose (compose (groupbyR (compose (name) (pi2))) ((swap (lrTopo)) (x))) (deify)) (y)))
# define
orTopo = Ω(R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg), doc="detects the topological relations between a set of objects and a set of regions", derived = lambda x,y: prod3 (apply (compose (compose (groupbyR (compose (name) (pi2))) ((swap (loTopo)) (x))) (deify)) (y)))


# Network operations
# primitive
nbuild = Ω(R3a(Obj, Reg, Ratio) ** R3(Obj, Ratio, Obj), doc="build a network from objects with impedance values", derived = None)
# primitive
nDist = Ω(R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj), doc="compute network distances between objects", derived = None)
# primitive
lVis = Ω(R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc), doc="build a visibility relation between locations using a DEM", derived = None)
# primitive
gridgraph = Ω(R2(Loc, Loc) ** R2(Loc, Ratio) ** R3(Loc, Ratio, Loc), doc="build a gridgraph using some location field and some impedance field", derived =None)
# primitive
lgDist = Ω(R3(Loc, Ratio, Loc) ** R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc), doc="compute gridgraph distances between locations", derived=None)

# Amount operations
fcont = Ω(lambda x, y:
    (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | x @ Qlt | y @ Qlt, doc="summarizes the content of a field within a region", derived=lambda f, x, r: f (subset (x) (deify (r))))
# define
ocont = Ω(R2(Obj, Reg) ** Reg ** Count, doc="counts the number of objects within a region", derived= lambda x,y: get (pi2 (groupbyR (count) (select (eq) (orTopo (x) (nest (y))) (in_)))))
# define
fcover = Ω(lambda x:
    R2(Loc, x) ** R1(x) ** R1(Loc) | x @ Qlt, doc="measures the spatial coverage of a field that is constrained to certain field values", derived= lambda x,y: pi1 (subset (x) (y)))
# define
ocover = Ω(R2(Obj, Reg) ** R1(Obj) ** Reg, doc="measures the spatial coverage of a collection of objects", derived=lambda x,y: merge (pi2 (subset (x) (y))))

###########################################################################
# Functional and Relational transformations


# Functional operators

# primitive
compose = Ω(lambda α, β, γ:
    (β ** γ) ** (α ** β) ** (α ** γ),
    doc="compose unary functions",
    derived=None
)

# primitive
compose2 = Ω(lambda α, β, γ, δ:
    (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ),
    doc="compose binary functions",
    derived=None
)

# primitive
swap = Ω(lambda α, β, γ:
    (α ** β ** γ) ** (β ** α ** γ),
    doc="swap binary function inputs",
    derived=None
)

# primitive
id_ = Ω(lambda α: α ** α,
        doc="identity",
        derived=None
        )

# primitive
apply = Ω(lambda x, y:
    (x ** y) ** R1(x) ** R2(x, y),
    doc="applying a function to a collection",
    derived=None
)


# Set operations

# primitive
nest = Ω(type=lambda x: x ** R1(x), doc="put value in unary relation", derived=None)
# primitive
nest2 = Ω(type=lambda x, y: x ** y ** R2(x, y), doc="put values in binary relation", derived=None)
# primitive
nest3 = Ω(type=lambda x, y, z: x ** y ** z ** R3(x, y, z), doc="put values in ternary relation", derived=None)
# primitive
add = Ω(type=lambda x: R1(x) ** x ** R1(x), doc="add value to unary relation", derived=None)
# primitive
get = Ω(lambda x: R1(x) ** x, doc="get some value from unary relation", derived=None)
# primitive
inrel = Ω(lambda x: x ** R1(x) ** Bool, doc="whether some value is in a relation", derived=None)

# define: relunion (add (nest (regions x)) (regions y))
set_union = Ω(
    type=lambda rel:
    rel ** rel ** rel,
    doc="union of two relations",
    derived = None
)

# primitive
set_diff = Ω(lambda rel:
    rel ** rel ** rel,
    doc="difference of two relations",
    derived = None
)

# define: set_diff rel1 (set_diff rel1 rel2)
set_inters = Ω(lambda rel:
    rel ** rel ** rel,
    doc="intersection of two relations",
    derived = lambda x, y: set_diff (x) (set_diff (x) (y))
)
# primitive
relunion = Ω(lambda rel:
    R1(rel) ** rel | rel @ operators(R1, R2, R3),
    doc="union of a set of relations",
    derived = None
)

# A constructor for quantified relations. prod generates a cartesian product as
# a nested binary relation. prod3 generates a quantified relation from two
# nested binary relations. The keys of the nested relations become two keys of
# the quantified relation.
# define: apply1 (compose ((swap apply1) (objectratios x2)) ratio) (ratiofield x1)
prod = Ω(lambda x, y, z, u, w:
    (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u)),
         doc= "A constructor for quantified relations. Prod generates a cartesian product of two relations as a nested binary relation.",
         derived=lambda f, x, y: apply1 (compose ((swap (apply1)) (y)) (f)) (x)
)

# primitive
prod3 = Ω(lambda x, y, z:
    R2(z, R2(x, y)) ** R3(x, y, z),
    doc= "prod3 generates a quantified relation from two nested binary relations. The keys of the nested relations become two keys of the quantified relation.",
        derived=None
)

# Projection (π). Projects a given relation to one of its attributes, resulting
# in a collection. Projection is also possible for multiple attributes.

# primitive
pi1 = Ω(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=1),
        doc="projects a given relation to the first attribute, resulting in a collection",
        derived=None
        )
# primitive
pi2 = Ω(lambda rel, x:
    rel ** R1(x)
    | rel @ operators(R1, R2, R3, param=x, at=2),
        doc="projects a given relation to the second attribute, resulting in a collection",
        derived=None
        )
# primitive
pi3 = Ω(lambda x: R3(_, _, x) ** R1(x),
        doc="projects a given ternary relation to the third attribute, resulting in a collection",
        derived=None)
# primitive
pi12 = Ω(lambda x, y: R3(x, y, _) ** R2(x, y),
         doc= "projects a given ternary relation to the first two attributes",
         derived=None)
# primitive
pi23 = Ω(lambda x, y: R3(_, x, y) ** R2(x, y),
        doc= "projects a given ternary relation to the last two attributes",
         derived=None)


# Selection (σ). Selects a subset of the relation using a constraint on
# attribute values, like equality (eq) or order (leq). Used to be sigmae
# and sigmale.

# primitive
select = Ω(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** y ** rel
    | rel @ operators(R1, R2, R3, R3a, param=x),
           doc="Selects a subset of a relation using a constraint on one attribute, like equality (eq) or order (leq)",
           derived=None)

# Select with subset. Subset a relation to those tuples having an attribute
# value contained in a collection.
# primitive
subset = Ω(lambda x, rel:
    rel ** R1(x) ** rel
    | rel @ operators(R1, R2, R3, R3a, param=x),
     doc="Subset a relation to those tuples having an attribute value contained in a collection",
     derived=lambda r, c: select (inrel, r, c))

# primitive
select2 = Ω(lambda x, y, rel:
    (x ** y ** Bool) ** rel ** rel
    | rel @ operators(R1, R2, R3, R3a, param=x)
    | rel @ operators(R1, R2, R3, R3a, param=y),
    doc ="Selects a subset of a relation using a constraint on two attributes, like equality (eq) or order (leq)",
    derived=None
)


# Join of two unary concepts, like a table join.
# primitive
join = Ω(lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z),
         doc= "Join of two unary concepts, like a table join",
         derived=None
         )



# functions to handle multiple attributes (with 1 key)
# define: prod3 (pi12 (select2 eq (prod3 (apply1 (compose ((swap apply1) (boolfield x1)) nest2) (ratiofield x2)))))
join_attr = Ω(lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z), derived=None)
get_attrL = Ω(lambda x, y, z: R3a(x, y, z) ** R2(x, y), derived=None)
get_attrR = Ω(lambda x, y, z: R3a(x, y, z) ** R2(x, z), derived=None)



# Join (⨝*). Substitute the quality of a quantified relation to some
# quality of one of its keys. Used to be bowtie*.
# define: prod3 (apply1 (subset (objectregions x2)) (groupbyL pi1 (rationetwork x1)))
join_key = Ω(lambda x, q1, y, rel, q2:
    R3(x, q1, y) ** rel ** R3(x, q2, y)
    | rel @ [R2(x, q2), R2(y, q2)],
             doc= "Substitute the quality of a quantified relation to some quality of one of its keys.",
             derived= None #lambda x, y: prod3 (apply1 (subset (y)) (groupbyL (pi1) (x)))
             )

# Join with unary function. Generate a unary concept from one other unary
# concept of the same type. Used to be join_fa/join_with1.
# define:
apply1 = Ω(lambda x1, x2, y:
    (x1 ** x2) ** R2(y, x1) ** R2(y, x2), doc="Join with unary function. Generates a unary concept from one other unary concept using a function",
    derived=lambda f, y: join (y) (apply (f) (pi2 (y))))

# Join with binary function (⨝_f). Generate a unary concept from two other
# unary concepts of the same type. Used to be bowtie_ratio/join_with2 and others.
# define
apply2 = Ω(lambda x1, x2, x3, y:
    (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3),
           doc="Join with binary function. Generates a unary concept from two other unary concepts of the same type",
           derived = lambda f, x,y: pi12 (select2 (eq) (prod3 (prod (f) (x) (y))))
           )

# Group by (β). Group quantified relations by the left (right) key,
# summarizing lists of quality values with the same key value into a new
# value per key, resulting in a unary core concept relation.

# primitive
groupbyL = Ω(lambda rel, l, q1, q2, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(l, q2)
    | rel @ [R1(r), R2(r, q1)],
             doc= "Group quantified relations by the left key, summarizing lists of quality values with the same key value into a new value per key, resulting in a unary concept.",
             derived=None
             )

# primitive
groupbyR = Ω(lambda rel, q2, l, q1, r:
    (rel ** q2) ** R3(l, q1, r) ** R2(r, q2)
    | rel @ [R1(l), R2(l, q1)],
            doc= "Group quantified relations by the right key, summarizing lists of quality values with the same key value into a new value per key, resulting in a unary concept.",
             derived=None
            )

# Group by qualities of binary relations
# example:  groupby count (objectregions x)
# primitive
groupby = Ω(lambda l, q, y:
    (R1(l) ** q) ** R2(l, y) ** R2(y, q),
            doc= "Group by qualities of binary relations",
            derived = None
            )


##############################################################################
# Generate an algebra out of all definitions in this module
cct = TransformationAlgebra(**globals())
