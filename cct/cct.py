"""
Module containing the core concept transformation algebra. Usage:

    >>> from cct import cct
    >>> cct.parse("pi1 (objects data)")
    R1(Obj)
     ├─╼ pi1 : rel ** R1(x) | rel @ [R1(x), R2(x, _), R3(x, _, _)]
     └─╼ objects data : R1(Obj)
"""

from transformation_algebra import \
    Type, operators, _, Data, Operation, TransformationAlgebra
from transformation_algebra.rdf import AlgebraNamespace


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
Contour = R2(Ord, Reg)
ContourLine = R2(Itv, Reg)
PointMeasures = R2(Reg, Itv)
AmountPatches = R2(Reg, Nom)
BooleanCoverages = R2(Bool, Reg)
NominalCoverages = R2(Nom, Reg)
RatioNetwork = R3(Obj, Ratio, Obj)


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

# Derivations

ratio = Operation(
    type=Ratio ** Ratio ** Ratio
)
product = Operation(
    type=Ratio ** Ratio ** Ratio
)
leq = Operation(
    doc="less than or equal",
    type=Ord ** Ord ** Bool
)
eq = Operation(
    doc="equal",
    type=Val ** Val ** Bool
)
conj = Operation(
    doc="conjunction",
    type=Bool ** Bool ** Bool
)
notj = Operation(
    doc="logical negation",
    type=Bool ** Bool
)
disj = Operation(
    doc="disjunction",
    type=Bool ** Bool ** Bool,
    derived=lambda x: compose2(notj, conj, x)
)
classify = Operation(
    doc="classification table",
    type=Itv ** Ord
)

# Aggregations of collections

count = Operation(
    doc="count objects",
    type=R1(Obj) ** Count
)
size = Operation(
    doc="measure size",
    type=R1(Loc) ** Ratio
)
merge = Operation(
    doc="merge regions",
    type=R1(Reg) ** Reg,
    derived=lambda x: reify(relunion(pi2(apply(deify, x))))
)
centroid = Operation(
    doc="measure centroid",
    type=R1(Loc) ** Loc
)
name = Operation(
    doc="combine nominal values",
    type=R1(Nom) ** Nom
)

# Statistical operations

avg = Operation(
    doc="average",
    type=lambda y: R2(Val, y) ** y | y @ Itv
)
min = Operation(
    doc="minimum",
    type=lambda y: R2(Val, y) ** y | y @ Ord
)
max = Operation(
    doc="maximum",
    type=lambda y: R2(Val, y) ** y | y @ Ord
)
sum = Operation(
    doc="summing up values",
    type=lambda y: R2(Val, y) ** y | y @ Ratio
)
contentsum = Operation(
    doc="summing up content amounts (regions and their values)",
    type=lambda x: R2(Reg, x) ** R2(Reg, x) | x @ Ratio,
    derived=lambda x: nest2(merge(pi1(x)), sum(x))
)
coveragesum = Operation(
    doc="summing up nominal coverages",
    type=R2(Nom, Reg) ** R2(Nom, Reg),
    derived=lambda x: nest2(name(pi1(x)), merge(pi2(x)))
)


##########################################################################
# Geometric transformations

interpol = Operation(
    doc="spatial point interpolation",
    type=lambda x: R2(Reg, x) ** R1(Loc) ** R2(Loc, x) | x @ Itv
)
extrapol = Operation(
    doc="buffering, defined in terms of some distance (given as parameter)",
    type=R2(Obj, Reg) ** R2(Loc, Bool),
    derived=lambda x: apply1(
        leq(ratioV),
        groupbyL(min, loDist(deify(region), x)))
)
arealinterpol = Operation(
    doc="areal interpolation",
    type=R2(Reg, Ratio) ** R1(Reg) ** R2(Reg, Ratio)
)
slope = Operation(
    doc="areal interpolation",
    type=R2(Loc, Itv) ** R2(Loc, Ratio),
)
aspect = Operation(
    doc="spatial aspect (cardinal direction) from DEM",
    type=R2(Loc, Itv) ** R2(Loc, Ratio),
)
flowdirgraph = Operation(
    doc="flow direction graph from DEM (location field)", 
    type=R2(Loc, Itv) ** R2(Loc, Loc)
)
accumulate = Operation(
    doc="finds all locations reachable from a given location",
    type=R2(Loc, Loc) ** R2(Loc, R1(Loc))
)

# Conversions

reify = Operation(
    doc="make a region from locations",
    type=R1(Loc) ** Reg
)
deify = Operation(
    doc="make locations from a region",
    type=Reg ** R1(Loc)
)
objectify = Operation(
    doc="interpet a name as an object",
    type=Nom ** Obj
)
nominalize = Operation(
    doc="interpret an object as a name",
    type=Obj ** Nom
)
getobjectnames = Operation(
    doc="make objects from names",
    type=R1(Nom) ** R2(Obj, Nom),
    derived=lambda x: apply(nominalize, pi2(apply(objectify, x)))
)
invert = Operation(
    doc="invert a field, generating a coverage",
    type=lambda x: R2(Loc, x) ** R2(x, Reg) | x @ Val,
    derived=lambda x: groupby(reify, x)
)
revert = Operation(
    doc="invert a coverage to a field",
    type=lambda x: R2(x, Reg) ** R2(Loc, x) | x @ Val,
    derived=lambda x: groupbyL(
        compose(get, pi1),
        join_key(
            select(eq, lTopo(deify(merge(pi2(x))), merge(pi2(x))), in_),
            groupby(get, x)
        )
    )
)
getamounts = Operation(
    doc="get amounts from object based amount qualities",
    type=lambda x: R3a(Obj, Reg, x) ** R2(Reg, x) | x @ Ratio,
    derived=lambda x: join(groupby(get, get_attrL(x)), get_attrR(x))
)

# Operators on quantified relations

lDist = Operation(
    doc="computes Euclidean distances between locations",
    type=R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
)
loDist = Operation(
    doc="computes Euclidean distances between locations and objects",
    type=R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj),
    derived=lambda x, y: prod3(apply1(
        compose(groupbyL(min), lDist(x)),
        apply1(deify, y)
    ))
)
oDist = Operation(
    doc="computes Euclidean distances between objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj),
    derived=lambda x, y: prod3(apply1(
        compose(groupbyR(min), swap(loDist, x)),
        apply1(deify, y)
    ))
)
lTopo = Operation(
    doc=("detects the topological position of locations "
         "on a region (in, out, boundary)"),
    type=R1(Loc) ** Reg ** R3(Loc, Nom, Reg),
)
loTopo = Operation(
    doc=("detects the topological position of locations "
         "on objects (in, out, boundary)"),
    type=R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Nom, Obj),
    derived=lambda x, y: prod3(apply1(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
oTopo = Operation(
    doc="detects the topological relations between two sets of objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj),
    derived=lambda x, y: prod3(apply1(
        compose(groupbyR(compose(name, pi2)), swap(loTopo, x)),
        apply1(deify, y)
    ))
)
lrTopo = Operation(
    doc=("detects the topological position of locations "
         "on regions (in, out, boundary)"),
    type=R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg),
    derived=lambda x, y: prod3(apply(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
rTopo = Operation(
    R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg),
    doc="detects the topological relations between two sets of regions",
    derived=lambda x, y: prod3(apply(
        compose(
            compose(groupbyR(compose(name, pi2)), swap(lrTopo, x)),
            deify),
        y
    ))
)
orTopo = Operation(
    doc=("detects the topological relations between a set of objects "
        "and a set of regions"),
    type=R2(Obj, Reg) ** R1(Reg) ** R3(Obj, Nom, Reg),
    derived=lambda x, y: prod3(apply(
        compose(compose(groupbyR(compose(name, pi2)), swap(loTopo, x)), deify),
        y
    ))
)

# Network operations

nbuild = Operation(
    doc="build a network from objects with impedance values",
    type=R3a(Obj, Reg, Ratio) ** R3(Obj, Ratio, Obj)
)
nDist = Operation(
    doc="compute network distances between objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj)
        ** R3(Obj, Ratio, Obj)
)
lVis = Operation(
    doc="build a visibility relation between locations using a DEM",
    type=R1(Loc) ** R1(Loc) ** R2(Loc, Itv) ** R3(Loc, Bool, Loc)
)
gridgraph = Operation(
    doc="build a gridgraph using some location field and some impedance field",
    type=R2(Loc, Loc) ** R2(Loc, Ratio) ** R3(Loc, Ratio, Loc)
)
lgDist = Operation(
    doc="compute gridgraph distances between locations",
    type=R3(Loc, Ratio, Loc) ** R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
)

# Amount operations
fcont = Operation(
    doc="summarizes the content of a field within a region",
    type=lambda x, y: (
        (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y | x @ Qlt | y @ Qlt),
    derived=lambda f, x, r: f(subset(x, deify(r)))
)
ocont = Operation(
    doc="counts the number of objects within a region",
    type=R2(Obj, Reg) ** Reg ** Count,
    derived=lambda x, y: get(pi2(
        groupbyR(count, select(eq, orTopo(x, nest(y)), in_))
    ))
)
fcover = Operation(
    doc=("measures the spatial coverage of a field that is constrained "
         "to certain field values"),
    type=lambda x: R2(Loc, x) ** R1(x) ** R1(Loc) | x @ Qlt,
    derived=lambda x, y: pi1(subset(x, y))
)
ocover = Operation(
    doc="measures the spatial coverage of a collection of objects",
    type=R2(Obj, Reg) ** R1(Obj) ** Reg,
    derived=lambda x, y: merge(pi2(subset(x, y)))
)

###########################################################################
# Functional and Relational transformations

# Functional operators

compose = Operation(
    doc="compose unary functions",
    type=lambda α, β, γ: (β ** γ) ** (α ** β) ** (α ** γ),
    derived=lambda f, g, x: f(g(x))
)
compose2 = Operation(
    doc="compose binary functions",
    type=lambda α, β, γ, δ: (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ),
    derived=lambda f, g, x, y: f(g(x, y))
)
swap = Operation(
    doc="swap binary function inputs",
    type=lambda α, β, γ: (α ** β ** γ) ** (β ** α ** γ),
    derived=lambda f, x, y: f(y, x)
)
id_ = Operation(
    doc="identity",
    type=lambda α: α ** α,
    derived=lambda x: x
)
apply = Operation(
    doc="applying a function to a collection",
    type=lambda x, y: (x ** y) ** R1(x) ** R2(x, y)
)

# Set operations

nest = Operation(
    doc="put value in unary relation",
    type=lambda x: x ** R1(x)
)
nest2 = Operation(
    doc="put values in binary relation",
    type=lambda x, y: x ** y ** R2(x, y)
)
nest3 = Operation(
    type=lambda x, y, z: x ** y ** z ** R3(x, y, z),
    doc="put values in ternary relation"
)
add = Operation(
    doc="add value to unary relation",
    type=lambda x: R1(x) ** x ** R1(x),
)
get = Operation(
    doc="get some value from unary relation",
    type=lambda x: R1(x) ** x
)
inrel = Operation(
    doc="whether some value is in a relation",
    type=lambda x: x ** R1(x) ** Bool,
)
set_union = Operation(
    doc="union of two relations",
    type=lambda rel: rel ** rel ** rel,
    derived=lambda x, y: relunion(add(nest(x), y))
)
set_diff = Operation(
    doc="difference of two relations",
    type=lambda rel: rel ** rel ** rel
)
set_inters = Operation(
    doc="intersection of two relations",
    type=lambda rel: rel ** rel ** rel,
    derived=lambda x, y: set_diff(x, set_diff(x, y))
)
relunion = Operation(
    doc="union of a set of relations",
    type=lambda rel: R1(rel) ** rel | rel @ operators(R1, R2, R3)
)
prod = Operation(
    doc=("A constructor for quantified relations. Prod generates a cartesian "
         "product of two relations as a nested binary relation."),
    type=lambda x, y, z, u, w:
        (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u)),
    derived=lambda f, x, y: apply1(compose(swap(apply1, y), f), x)
)
prod3 = Operation(
    doc=("prod3 generates a quantified relation from two nested binary "
        "relations. The keys of the nested relations become two keys of "
        "the quantified relation."),
    type=lambda x, y, z: R2(z, R2(x, y)) ** R3(x, y, z),
)

# Projection (π)

pi1 = Operation(
    doc=("projects a given relation to the first attribute, resulting in a "
         "collection"),
    type=lambda rel, x:
        rel ** R1(x) | rel @ operators(R1, R2, R3, param=x, at=1),
)
pi2 = Operation(
    doc=("projects a given relation to the second attribute, resulting in a "
         "collection"),
    type=lambda rel, x:
        rel ** R1(x) | rel @ operators(R1, R2, R3, param=x, at=2),
)
pi3 = Operation(
    doc=("projects a given ternary relation to the third attribute, resulting "
         "in a collection"),
    type=lambda x: R3(_, _, x) ** R1(x)
)
pi12 = Operation(
    doc="projects a given ternary relation to the first two attributes",
    type=lambda x, y: R3(x, y, _) ** R2(x, y)
)
pi23 = Operation(
    doc="projects a given ternary relation to the last two attributes",
    type=lambda x, y: R3(_, x, y) ** R2(x, y)
)

# Selection (σ)

select = Operation(
    doc=("Selects a subset of a relation using a constraint on one "
         "attribute, like equality (eq) or order (leq)"),
    type=lambda x, y, rel:
        (x ** y ** Bool) ** rel ** y ** rel \
        | rel @ operators(R1, R2, R3, R3a, param=x)
)
subset = Operation(
    doc=("Subset a relation to those tuples having an attribute value "
         "contained in a collection"),
    type=lambda x, rel:
        rel ** R1(x) ** rel | rel @ operators(R1, R2, R3, R3a, param=x),
    derived=lambda r, c: select(inrel, r, c)
)

select2 = Operation(
    doc=("Selects a subset of a relation using a constraint on two "
         "attributes, like equality (eq) or order (leq)"),
    type=lambda x, y, rel:
        (x ** y ** Bool) ** rel ** rel
        | rel @ operators(R1, R2, R3, R3a, param=x)
        | rel @ operators(R1, R2, R3, R3a, param=y)
)

# Join (⨝)

join = Operation(
    doc="Join of two unary concepts, like a table join",
    type=lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z)
)

# functions to handle multiple attributes (with 1 key)
join_attr = Operation(
    type=lambda x, y, z: R2(x, y) ** R2(x, z) ** R3a(x, y, z),
    # derived=lambda x1, x2: prod3(pi12(select2(
    #     eq,
    #     prod3(apply1(compose(swap(apply1, x1), nest2), x2))
    # )))
)
get_attrL = Operation(
    type=lambda x, y, z: R3a(x, y, z) ** R2(x, y),
    derived=None
)
get_attrR = Operation(
    type=lambda x, y, z: R3a(x, y, z) ** R2(x, z),
    derived=None
)

join_key = Operation(
    doc=("Substitute the quality of a quantified relation to some quality "
         "of one of its keys."),
    type=lambda x, q1, y, rel, q2:
        R3(x, q1, y) ** rel ** R3(x, q2, y) | rel @ [R2(x, q2), R2(y, q2)],
    # derived=lambda x, y: prod3(apply1(subset(y), groupbyL(pi1, x)))
)

apply1 = Operation(
    doc=("Join with unary function. Generates a unary concept from one "
         "other unary concept using a function"),
    type=lambda x1, x2, y:
        (x1 ** x2) ** R2(y, x1) ** R2(y, x2),
    derived=lambda f, y: join(y, apply(f, pi2(y)))
)
apply2 = Operation(
    doc=("Join with binary function. Generates a unary concept from two "
         "other unary concepts of the same type"),
    type=lambda x1, x2, x3, y:
        (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3),
    derived=lambda f, x, y: pi12(select2(eq, prod3(prod(f, x, y))))
)

groupbyL = Operation(
    doc=("Group quantified relations by the left key, summarizing lists "
         "of quality values with the same key value into a new value per "
         "key, resulting in a unary concept."),
    type=lambda rel, l, q1, q2, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(l, q2) | rel @ [R1(r), R2(r, q1)],
)
groupbyR = Operation(
    doc=("Group quantified relations by the right key, summarizing lists of "
         "quality values with the same key value into a new value per key, "
         "resulting in a unary concept."),
    type=lambda rel, q2, l, q1, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(r, q2) | rel @ [R1(l), R2(l, q1)]
)
groupby = Operation(
    doc="Group by qualities of binary relations",
    type=lambda l, q, y:
        (R1(l) ** q) ** R2(l, y) ** R2(y, q),
)


##############################################################################
# Generate an algebra out of all definitions in this module
cct = TransformationAlgebra()
cct.add(**globals())

CCT = AlgebraNamespace("https://github.com/quangis/cct#", cct)
