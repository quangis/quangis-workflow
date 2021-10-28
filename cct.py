# type: ignore
"""
Module containing the core concept transformation algebra. Usage:

    >>> from cct import cct
    >>> cct.parse("pi1 (objects data)")
    R1(Obj)
     ├─╼ pi1 : rel ** R1(x) | rel @ [R1(x), R2(x, _), R3(x, _, _)]
     └─╼ objects data : R1(Obj)
"""

from transformation_algebra import Type, with_parameters, _, Operator, \
    Language, LanguageNamespace


##############################################################################
# Types and type synonyms

Val = Type.declare()
Obj = Type.declare(supertype=Val)  # O
Reg = Type.declare(supertype=Val)  # S
Loc = Type.declare(supertype=Val)  # L
Qlt = Type.declare(supertype=Val)  # Q
Nom = Type.declare(supertype=Qlt)
Bool = Type.declare(supertype=Nom)
Ord = Type.declare(supertype=Nom)
Itv = Type.declare(supertype=Ord)
Ratio = Type.declare(supertype=Itv)
Count = Type.declare(supertype=Ratio)
R1 = Type.declare(params=1)  # Collections
R2 = Type.declare(params=2)  # Unary core concepts, 1 key (left)
R3 = Type.declare(params=3)  # Quantified relation, 2 keys (l & r)
R3a = Type.declare(params=3)  # Ternary relation, 1 key (left)

SpatialField = R2(Loc, Qlt)
InvertedField = R2(Qlt, Reg)
FieldSample = R2(Reg, Qlt)
ObjectExtent = R2(Obj, Reg)
ObjectQuality = R2(Obj, Qlt)
NominalField = R2(Loc, Nom)
BooleanField = R2(Loc, Bool)
NominalInvertedField = R2(Nom, Reg)
BooleanInvertedField = R2(Bool, Reg)
Contour = R2(Ord, Reg)
ContourLine = R2(Itv, Reg)
PointMeasures = R2(Reg, Itv)
AmountPatches = R2(Reg, Nom)
BooleanCoverages = R2(Bool, Reg)
NominalCoverages = R2(Nom, Reg)
RatioNetwork = R3(Obj, Ratio, Obj)


##############################################################################
# Data inputs

# Reintroducing these for now to make sure the tests still work
objectnominals = Operator(R2(Obj, Nom))
objectcounts = Operator(R2(Obj, Count))

test = Operator(
    type=lambda x: x,
    doc="This is a data input of any type, strictly for testing."
)

pointmeasures = Operator(R2(Reg, Itv))
amountpatches = Operator(R2(Reg, Nom))
countamounts = Operator(R2(Reg, Count))
ratioamounts = Operator(R2(Reg, Ratio))
boolcoverages = Operator(R2(Bool, Reg))
boolratio = Operator(R2(Bool, Ratio))
nomcoverages = Operator(R2(Nom, Reg))
nomsize = Operator(R2(Nom, Ratio))
contour = Operator(R2(Ord, Reg))
contourline = Operator(R2(Itv, Reg))
objectregions = Operator(R2(Obj, Reg))
objectratios = Operator(R2(Obj, Ratio))
objectregionratios = Operator(R3a(Obj, Reg, Ratio))
objectregionnominals = Operator(R3a(Obj, Reg, Nom))
objectregioncounts = Operator(R3a(Obj, Reg, Count))
objectregionattr = Operator(lambda x: R3a(Obj, Reg, x))
field = Operator(R2(Loc, Ratio))
nomfield = Operator(R2(Loc, Nom))
boolfield = Operator(R2(Loc, Bool))
ordfield = Operator(R2(Loc, Ord))
itvfield = Operator(R2(Loc, Itv))
ratiofield = Operator(R2(Loc, Ratio))
locationfield = Operator(R2(Loc, Loc))
object = Operator(Obj)
objects = Operator(R1(Obj))
region = Operator(Reg)
regions = Operator(R1(Reg))
locs = Operator(R1(Loc))
in_ = Operator(Nom)
contains = Operator(Nom)
out = Operator(Nom)
noms = Operator(R1(Nom))
ratios = Operator(R1(Ratio))
countV = Operator(Count)
ratioV = Operator(Ratio)
interval = Operator(Itv)
ordinal = Operator(Ord)
nominal = Operator(Nom)
true = Operator(Bool)
rationetwork = Operator(R3(Obj, Ratio, Obj))

###########################################################################
# Math/stats transformations

# Derivations

ratio = Operator(
    type=Ratio ** Ratio ** Ratio
)
product = Operator(
    type=Ratio ** Ratio ** Ratio
)
leq = Operator(
    "less than or equal",
    type=Ord ** Ord ** Bool
)
eq = Operator(
    "equal",
    type=Val ** Val ** Bool
)
conj = Operator(
    "conjunction",
    type=Bool ** Bool ** Bool
)
notj = Operator(
    "logical negation",
    type=Bool ** Bool
)
disj = Operator(
    "disjunction",
    type=Bool ** Bool ** Bool,
    define=lambda x: compose2(notj, conj, x)
)
classify = Operator(
    "classification table",
    type=Itv ** Ord
)

# Aggregations of collections

count = Operator(
    "count objects",
    type=R1(Obj) ** Count
)
size = Operator(
    "measure size",
    type=R1(Loc) ** Ratio
)
merge = Operator(
    "merge regions",
    type=R1(Reg) ** Reg,
    define=lambda x: reify(relunion(pi2(apply(deify, x))))
)
centroid = Operator(
    "measure centroid",
    type=R1(Loc) ** Loc
)
name = Operator(
    "combine nominal values",
    type=R1(Nom) ** Nom
)

# Statistical operations

avg = Operator(
    "average",
    type=lambda y: R2(Val, y) ** y | y @ Itv
)
min = Operator(
    "minimum",
    type=lambda y: R2(Val, y) ** y | y @ Ord
)
max = Operator(
    "maximum",
    type=lambda y: R2(Val, y) ** y | y @ Ord
)
sum = Operator(
    "summing up values",
    type=lambda y: R2(Val, y) ** y | y @ Ratio
)
contentsum = Operator(
    "summing up content amounts (regions and their values)",
    type=lambda x: R2(Reg, x) ** R2(Reg, x) | x @ Ratio,
    define=lambda x: nest2(merge(pi1(x)), sum(x))
)
coveragesum = Operator(
    "summing up nominal coverages",
    type=R2(Nom, Reg) ** R2(Nom, Reg),
    define=lambda x: nest2(name(pi1(x)), merge(pi2(x)))
)


##########################################################################
# Geometric transformations

interpol = Operator(
    "spatial point interpolation",
    type=lambda x: R2(Reg, x) ** R1(Loc) ** R2(Loc, x) | x @ Itv
)
extrapol = Operator(
    "buffering, defined in terms of some distance (given as parameter)",
    type=R2(Obj, Reg) ** R2(Loc, Bool),
    define=lambda x: apply1(
        leq(ratioV),
        groupbyL(min, loDist(deify(region), x)))
)
arealinterpol = Operator(
    "areal interpolation",
    type=R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio)
)
slope = Operator(
    "slope",
    type=R2(Loc, Itv) ** R2(Loc, Ratio),
)
aspect = Operator(
    "spatial aspect (cardinal direction) from DEM",
    type=R2(Loc, Itv) ** R2(Loc, Ratio),
)
flowdirgraph = Operator(
    "flow direction graph from DEM (location field)",
    type=R2(Loc, Itv) ** R2(Loc, Loc)
)
accumulate = Operator(
    "finds all locations reachable from a given location",
    type=R2(Loc, Loc) ** R2(Loc, R1(Loc))
)

# Conversions

reify = Operator(
    "make a region from locations",
    type=R1(Loc) ** Reg
)
deify = Operator(
    "make locations from a region",
    type=Reg ** R1(Loc)
)
objectify = Operator(
    "interpet a name as an object",
    type=Nom ** Obj
)
nominalize = Operator(
    "interpret an object as a name",
    type=Obj ** Nom
)
getobjectnames = Operator(
    "make objects from names",
    type=R1(Nom) ** R2(Obj, Nom),
    define=lambda x: apply(nominalize, pi2(apply(objectify, x)))
)
invert = Operator(
    "invert a field, generating a coverage",
    type=lambda x: R2(Loc, x) ** R2(x, Reg) | x @ Val,
    define=lambda x: groupby(reify, x)
)
revert = Operator(
    "invert a coverage to a field",
    type=lambda x: R2(x, Reg) ** R2(Loc, x) | x @ Val,
    define=lambda x: groupbyL(
        compose(get, pi1),
        join_key(
            select(eq, lTopo(deify(merge(pi2(x))), merge(pi2(x))), in_),
            groupby(get, x)
        )
    )
)
getamounts = Operator(
    "get amounts from object based amount qualities",
    type=lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | x @ Ratio,
    define=lambda x: join(groupby(get, get_attrL(x)), get_attrR(x))
)

# Operators on quantified relations

lDist = Operator(
    "computes Euclidean distances between locations",
    type=R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
)
loDist = Operator(
    "computes Euclidean distances between locations and objects",
    type=R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj),
    define=lambda x, y: prod3(apply1(
        compose(groupbyL(min), lDist(x)),
        apply1(deify, y)
    ))
)
oDist = Operator(
    "computes Euclidean distances between objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj),
    define=lambda x, y: prod3(apply1(
        compose(groupbyR(min), swap(loDist, x)),
        apply1(deify, y)
    ))
)
lTopo = Operator(
    "detects the topological position of locations on a region (in, out, "
    "boundary)",
    type=R1(Loc) ** Reg ** R3(Loc, Nom, Reg),
)
loTopo = Operator(
    "detects the topological position of locations on objects (in, out, "
    "boundary)",
    type=R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj),
    define=lambda x, y: prod3(apply1(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
oTopo = Operator(
    "detects the topological relations between two sets of objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj),
    define=lambda x, y: prod3(apply1(
        compose(groupbyR(compose(name, pi2)), swap(loTopo, x)),
        apply1(deify, y)
    ))
)
lrTopo = Operator(
    "detects the topological position of locations on regions (in, out, "
    "boundary)",
    type=R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg),
    define=lambda x, y: prod3(apply(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
rTopo = Operator(
    "detects the topological relations between two sets of regions",
    type=R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg),
    define=lambda x, y: prod3(apply(
        compose(
            compose(groupbyR(compose(name, pi2)), swap(lrTopo, x)),
            deify),
        y
    ))
)
orTopo = Operator(
    "detects the topological relations between a set of objects and a set of "
    "regions",
    type=R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg),
    define=lambda x, y: prod3(apply(
        compose(compose(groupbyR(compose(name, pi2)), swap(loTopo, x)), deify),
        y
    ))
)

# Network operations

nbuild = Operator(
    "build a network from objects with impedance values",
    type=R3a(Obj, Reg, Ratio) ** R3(Obj, Ratio, Obj)
)
nDist = Operator(
    "compute network distances between objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
        ** R3(Obj, Ratio, Obj)
)
lVis = Operator(
    "build a visibility relation between locations using a DEM",
    type=R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)
)
gridgraph = Operator(
    "build a gridgraph using some location field and some impedance field",
    type=R2(Loc, Loc) ** R2(Loc, Ratio) ** R3(Loc, Ratio, Loc)
)
lgDist = Operator(
    doc="compute gridgraph distances between locations",
    type=R3(Loc, Ratio, Loc) ** R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
)

# Amount operations
fcont = Operator(
    "summarizes the content of a field within a region",
    type=lambda x, y: (
        (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | x @ Qlt | y @ Qlt),
    define=lambda f, x, r: f(subset(x, deify(r)))
)
ocont = Operator(
    "counts the number of objects within a region",
    type=R2(Obj, Reg) ** Reg ** Count,
    define=lambda x, y: get(pi2(
        groupbyR(count, select(eq, orTopo(x, nest(y)), in_))
    ))
)
fcover = Operator(
    "measures the spatial coverage of a field that is constrained to certain "
    "field values",
    type=lambda x: R2(Loc, x) ** R1(x) ** R1(Loc) | x @ Qlt,
    define=lambda x, y: pi1(subset(x, y))
)
ocover = Operator(
    "measures the spatial coverage of a collection of objects",
    type=R2(Obj, Reg) ** R1(Obj) ** Reg,
    define=lambda x, y: merge(pi2(subset(x, y)))
)

###########################################################################
# Functional and Relational transformations

# Functional operators

compose = Operator(
    "compose unary functions",
    type=lambda α, β, γ: (β ** γ) ** (α ** β) ** (α ** γ),
    define=lambda f, g, x: f(g(x))
)
compose2 = Operator(
    "compose binary functions",
    type=lambda α, β, γ, δ: (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ),
    define=lambda f, g, x, y: f(g(x, y))
)
swap = Operator(
    "swap binary function inputs",
    type=lambda α, β, γ: (α ** β ** γ) ** (β ** α ** γ),
    define=lambda f, x, y: f(y, x)
)
id_ = Operator(
    "identity",
    type=lambda α: α ** α,
    define=lambda x: x
)
apply = Operator(
    "applying a function to a collection",
    type=lambda x, y: (x ** y) ** R1(x) ** R2(x, y)
)

# Set operations

nest = Operator(
    "put value in unary relation",
    type=lambda x: x ** R1(x)
)
nest2 = Operator(
    "put values in binary relation",
    type=lambda x, y: x ** y ** R2(x, y)
)
nest3 = Operator(
    "put values in ternary relation",
    type=lambda x, y, z: x ** y ** z ** R3(x, y, z)
)
add = Operator(
    "add value to unary relation",
    type=lambda x: R1(x) ** x ** R1(x),
)
get = Operator(
    "get some value from unary relation",
    type=lambda x: R1(x) ** x
)
inrel = Operator(
    "whether some value is in a relation",
    type=lambda x: x ** R1(x) ** Bool,
)
set_union = Operator(
    "union of two relations",
    type=lambda rel: rel ** rel ** rel,
    define=lambda x, y: relunion(add(nest(x), y))
)
set_diff = Operator(
    "difference of two relations",
    type=lambda rel: rel ** rel ** rel
)
set_inters = Operator(
    "intersection of two relations",
    type=lambda rel: rel ** rel ** rel,
    define=lambda x, y: set_diff(x, set_diff(x, y))
)
relunion = Operator(
    "union of a set of relations",
    type=lambda rel: R1(rel) ** rel | rel @ with_parameters(R1, R2, R3)
)
prod = Operator(
    "A constructor for quantified relations. Prod generates a cartesian "
    "product of two relations as a nested binary relation.",
    type=lambda x, y, z, u, w:
        (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u)),
    define=lambda f, x, y: apply1(compose(swap(apply1, y), f), x)
)
prod3 = Operator(
    doc=("prod3 generates a quantified relation from two nested binary "
        "relations. The keys of the nested relations become two keys of "
        "the quantified relation."),
    type=lambda x, y, z: R2(z, R2(x, y)) ** R3(x, y, z),
)

# Projection (π)

pi1 = Operator(
    "projects a given relation to the first attribute, resulting in a "
    "collection",
    type=lambda rel, x:
        rel ** R1(x) | rel @ with_parameters(R1, R2, R3, param=x, at=1),
)
pi2 = Operator(
    "projects a given relation to the second attribute, resulting in a "
    "collection",
    type=lambda rel, x:
        rel ** R1(x) | rel @ with_parameters(R1, R2, R3, param=x, at=2),
)
pi3 = Operator(
    "projects a given ternary relation to the third attribute, resulting "
    "in a collection",
    type=lambda x: R3(_, _, x) ** R1(x)
)
pi12 = Operator(
    "projects a given ternary relation to the first two attributes",
    type=lambda x, y: R3(x, y, _) ** R2(x, y)
)
pi23 = Operator(
    "projects a given ternary relation to the last two attributes",
    type=lambda x, y: R3(_, x, y) ** R2(x, y)
)

# Selection (σ)

select = Operator(
    "Selects a subset of a relation using a constraint on one attribute, like "
    "equality (eq) or order (leq)",
    type=lambda x, y, rel:
        (x ** y ** Bool) ** rel ** y ** rel
        | rel @ with_parameters(R1, R2, R3, R3a, param=x)
)
subset = Operator(
    "Subset a relation to those tuples having an attribute value contained in "
    "a collection",
    type=lambda x, rel:
        rel ** R1(x) ** rel | rel @ with_parameters(R1, R2, R3, R3a, param=x),
    define=lambda r, c: select(inrel, r, c)
)

select2 = Operator(
    "Selects a subset of a relation using a constraint on two attributes, "
    "like equality (eq) or order (leq)",
    type=lambda x, y, rel:
        (x ** y ** Bool) ** rel ** rel
        | rel @ with_parameters(R1, R2, R3, R3a, param=x)
        | rel @ with_parameters(R1, R2, R3, R3a, param=y)
)

# Join (⨝)

join = Operator(
    "Join of two unary concepts, like a table join",
    type=lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z)
)

# functions to handle multiple attributes (with 1 key)
join_attr = Operator(
    type=lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z),
    # define=lambda x1, x2: prod3(pi12(select2(
    #     eq,
    #     prod3(apply1(compose(swap(apply1, x1), nest2), x2))
    # )))
)
get_attrL = Operator(
    type=lambda x, y, z: R3a(x, y, z) ** R2(x, y),
    define=None
)
get_attrR = Operator(
    type=lambda x, y, z: R3a(x, y, z) ** R2(x, z),
    define=None
)

join_key = Operator(
    "Substitute the quality of a quantified relation to some quality of one "
    "of its keys.",
    type=lambda x, q1, y, rel, q2:
        R3(x, q1, y) ** rel ** R3(x, q2, y) | rel @ [R2(x, q2), R2(y, q2)],
    # define=lambda x, y: prod3(apply1(subset(y), groupbyL(pi1, x)))
)

apply1 = Operator(
    "Join with unary function. Generates a unary concept from one other "
    "unary concept using a function",
    type=lambda x1, x2, y:
        (x1 ** x2) ** R2(y, x1) ** R2(y, x2),
    define=lambda f, y: join(y, apply(f, pi2(y)))
)
apply2 = Operator(
    "Join with binary function. Generates a unary concept from two other "
    "unary concepts of the same type"),
    type=lambda x1, x2, x3, y:
        (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3),
    define=lambda f, x, y: pi12(select2(eq, prod3(prod(f, x, y))))
)

groupbyL = Operator(
    "Group quantified relations by the left key, summarizing lists of "
    "quality values with the same key value into a new value per key, "
    "resulting in a unary concept.",
    type=lambda rel, l, q1, q2, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(l, q2) | rel @ [R1(r), R2(r, q1)],
)
groupbyR = Operator(
    "Group quantified relations by the right key, summarizing lists of "
    "quality values with the same key value into a new value per key, "
    "resulting in a unary concept.",
    type=lambda rel, q2, l, q1, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(r, q2) | rel @ [R1(l), R2(l, q1)]
)
groupby = Operator(
    "Group by qualities of binary relations",
    type=lambda l, q, y:
        (R1(l) ** q) ** R2(l, y) ** R2(y, q),
)


##############################################################################
# Generate an algebra out of all definitions in this module

cct = Language()
cct.add_scope(globals())
CCT = LanguageNamespace("https://github.com/quangis/cct#", cct)
