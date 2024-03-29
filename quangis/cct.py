# type: ignore
"""
Module containing the core concept transformation algebra. Usage:

    >>> from cct import cct
    >>> cct.parse("pi1 (objects data)")
    R1(Obj)
     ├─╼ pi1 : rel ** R1(x) | rel << [R1(x), R2(x, _), R3(x, _, _)]
     └─╼ objects data : R1(Obj)
"""

from transforge.type import Type, Constraint, \
    TypeInstance, TypeAlias, TypeOperator, \
    with_parameters, _, Top
from transforge.lang import Language
from transforge.expr import Operator, Source


# Types ######################################################################

Val = TypeOperator()
Obj = TypeOperator(supertype=Val)  # O
Reg = TypeOperator(supertype=Val)  # S
Loc = TypeOperator(supertype=Val)  # L
Qlt = TypeOperator(supertype=Val)  # Q
Nom = TypeOperator(supertype=Qlt)
Bool = TypeOperator(supertype=Nom)
Ord = TypeOperator(supertype=Nom)
Itv = TypeOperator(supertype=Ord)
Ratio = TypeOperator(supertype=Itv)
Count = TypeOperator(supertype=Ratio)
# R = TypeOperator(params=2)
R1 = TypeOperator(params=1)
R2 = TypeOperator(params=2)
R3 = TypeOperator(params=3)
List = TypeOperator(params =1)

# Previously, we had types that looked like R1(x), R3(x, y, z), etcetera.
# Everything is now expressed in terms of the R relation and Product/Unit
# types, like R(x, Unit) and R(x * z, y). There are some issues that need to be
# addressed before this fully works, so in the meantime, we use this type
# alias.

R = TypeAlias(lambda x, y: R2(x, y))
C = TypeAlias(lambda x: R1(x))

# Type synonyms ##############################################################

# R1 = TypeAlias(lambda x: R(x, Unit), Val)
# R2 = TypeAlias(lambda x, y: R(x, y), Val, Val)
# R3 = TypeAlias(lambda x, y, z: R(x * z, y), Val, Val, Val)


def with_param(on: Type, x: TypeInstance, at: int = None) -> Constraint:
    return on << tuple(with_parameters(R1, R2, R3, lambda x, y, z: R2(x, y * z),
        param=x, at=at))
    # """
    # Generate a list of instances of relations. The generated relations must
    # contain a certain parameter (at some index, if given).
    # """

    # # This is really hacky due to the fact that we can't have
    # # constraints-in-constraints.
    # c: list[TypeInstance] = []
    # if at is None or at == 1:
    #     c.append(Val * R(x, _))
    #     c.append(R(_, _) * R(x, _))
    #     c.append(Val * R(x * _, _))
    # if at is None or at == 2:
    #     c.append(Val * R(_, x))
    #     c.append(R(_, _) * R(_, x))
    #     c.append(Val * R(_ * x, _))
    #     c.append(Val * R(_, x * _))
    # if at is None or at == 3:
    #     c.append(Val * R(_, _ * x))
    #     c.appene(Val * R(_ * _, x))
    # (x * on)[c]
    # return on


Field = TypeAlias(lambda x: R2(Loc, x))
Amounts = TypeAlias(lambda x: R2(Reg, x) [x <= Qlt])
FieldSample = TypeAlias(R2(Reg, Qlt))
AmountPatches = TypeAlias(R2(Reg, Nom))
PointMeasures = TypeAlias(R2(Reg, Itv))
Coverages = TypeAlias(lambda x: R2(x, Reg) [x <= Qlt])
Contour = TypeAlias(R2(Ord, Reg))
ContourLine = TypeAlias(R2(Itv, Reg))
ObjectExtent = TypeAlias(R2(Obj, Reg))
RelationalField = TypeAlias(lambda x: R3(Loc, x, Loc) [x <= Qlt])
Network = TypeAlias(lambda x: R3(Obj, x, Obj) [x <= Qlt])
ObjectInfo = TypeAlias(lambda x: R2(Obj, Reg * x))  # Associate objects with
# both their extent and some quality

in_ = Operator(type=Nom)
out = Operator(type=Nom)
true = Operator(type=Bool)


# Math/stats transformations ##############################################

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
    body=lambda x: compose2(notj, conj, x)
)
classify = Operator(
    "classification table",
    type=Itv ** Ord
)
empty = Operator(
    "empty relation",
    type=lambda rel: rel ** Bool
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
    body=lambda x: reify(relunion(pi2(apply(deify, x))))
)
centroid = Operator(
    "measure centroid",
    type=R1(Loc) ** Loc
)
name = Operator(
    "combine nominal values",
    type=lambda x: R1(x) ** x [x <= Nom]
)

# Statistical operations

avg = Operator(
    "average",
    type=lambda y: R2(Val, y) ** y [y <= Itv]
)
min = Operator(
    "minimum",
    type=lambda y: R2(Val, y) ** y [y <= Ord]
)
max = Operator(
    "maximum",
    type=lambda y: R2(Val, y) ** y [y <= Ord]
)
sum = Operator(
    "summing up values",
    type=lambda y: R2(Val, y) ** y [y <= Ratio]
)
conslistrel = Operator(
    "construct list from relation",
    type=lambda x,y: R2(x, y) ** R2(x, List(y)),
    body= lambda x: apply1 (addlist (emptylist)) (x)
)
addlistrel = Operator(
    "add to list from relation",
    type=lambda x,y: R2(x, List(y)) ** R2(x, y) ** R2(x, List(y)),
    body= lambda x, y: apply2 (addlist) (x) (y)
)
diversity = Operator(
    "calculating diversity of values (entropy)",
    type=lambda x, y: R2(x, List(y)) ** R2(x, Ratio) [y <= Ratio]
)
contentsum = Operator(
    "summing up content amounts (regions and their values)",
    type=lambda x: R2(Reg, x) ** R2(Reg, x) [x <= Ratio],
    body=lambda x: nest2(merge(pi1(x)), sum(x))
)
coveragesum = Operator(
    "summing up nominal coverages",
    type=R2(Nom, Reg) ** R2(Nom, Reg),
    body=lambda x: nest2(name(pi1(x)), merge(pi2(x)))
)


# Geometric transformations ##############################################

interpol = Operator(
    "spatial point interpolation",
    type=lambda x: R2(Reg, x) ** R1(Loc) ** R2(Loc, x) [x <= Itv]
)
extrapol = Operator(
    "buffering, defined in terms of some distance (given as parameter)",
    type=R2(Obj, Reg) ** R2(Loc, Bool),
    body=lambda x: apply1(
        leq(~Ratio),
        groupbyL(min, loDist(deify(~Reg), x)))
)
arealinterpol = Operator(
    "areal interpolation",
    type=lambda x: R2(Reg, x) ** R1(Reg) ** R2(Reg, x) [x <= Ratio]
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
kernelDensity = Operator(
    "computes a field of distance and attribute - weighted density of objects",
    type=R2(Obj, Reg * Ratio) ** R2(Loc, Ratio),
    body=lambda x: groupbyL (compose(sum, (apply2(product, (get_attrR(x)))))) (loDist (Source(R1(Loc))) (get_attrL(x)))
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
    body=lambda x: apply(nominalize, pi2(apply(objectify, x)))
)
objectfromobjects = Operator(
    "make object from collection of objects",
    type=lambda x: R1(Obj) ** Obj
)
generateobjects = Operator(
    "make objects from other objects (e.g. random points)",
    type=lambda x: R2(Obj, Reg * x) ** R2(Obj, Reg * Nom)
)
generateobjectsfromrel= Operator(
    "make objects from object relations (e.g. routes)",
    type=R3(Obj, Reg, Obj) ** R2(Obj, Reg * Nom)
)
invert = Operator(
    "invert a field, generating a coverage",
    type=lambda x: R2(Loc, x) ** R2(x, Reg) [x < Val],
    body=lambda x: groupby(reify, x)
)
revert = Operator(
    "invert a coverage to a field",
    type=lambda x: R2(x, Reg) ** R2(Loc, x) [x < Val],
    body=lambda x: groupbyL(
        compose(get, pi1),
        join_key(
            select(eq, lTopo(deify(merge(pi2(x))), merge(pi2(x))), in_),
            groupby(get, x)
        )
    )
)
getamounts = Operator(
    "get amounts from object based amount qualities",
    type=lambda x: ObjectInfo(x) ** R2(Reg, x) [x <= Ratio],
    body=lambda x: join(groupby(get, get_attrL(x)), get_attrR(x))
)

intersect = Operator(
    "intersect two regions",
    type=Reg ** Reg ** Reg,
    body = lambda x, y: reify(set_inters(deify(x), deify(y)))
)

# Operators on quantified relations

lDist = Operator(
    "computes Euclidean distances between locations",
    type=R1(Loc) ** R1(Loc) ** R3(Loc, Ratio, Loc)
)
loDist = Operator(
    "computes Euclidean distances between locations and objects",
    type=R1(Loc) ** R2(Obj, Reg) ** R3(Loc, Ratio, Obj),
    body=lambda x, y: prod3(apply1(
        compose(groupbyL(min), lDist(x)),
        apply1(deify, y)
    ))
)
oDist = Operator(
    "computes Euclidean distances between objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Ratio, Obj),
    body=lambda x, y: prod3(apply1(
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
    body=lambda x, y: prod3(apply1(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
oTopo = Operator(
    "detects the topological relations between two sets of objects",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Nom, Obj),
    body=lambda x, y: prod3(apply1(
        compose(groupbyR(compose(name, pi2)), swap(loTopo, x)),
        apply1(deify, y)
    ))
)
lrTopo = Operator(
    "detects the topological position of locations on regions (in, out, "
    "boundary)",
    type=R1(Loc) ** R1(Reg) ** R3(Loc, Nom, Reg),
    body=lambda x, y: prod3(apply(
        compose(groupbyL(compose(get, pi2)), lTopo(x)),
        y
    ))
)
rTopo = Operator(
    "detects the topological relations between two sets of regions",
    type=R1(Reg) ** R1(Reg) ** R3(Reg, Nom, Reg),
    body=lambda x, y: prod3(apply(
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
    body=lambda x, y: prod3(apply(
        compose(compose(groupbyR(compose(name, pi2)), swap(loTopo, x)), deify),
        y
    ))
)

# Network operations

consIntersect = Operator(
    "constructs a quantified relation of intersections of object regions (excluding empty intersections)",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R3(Obj, Reg, Obj),
    body=lambda x, y: select (compose(notj,empty))(prod3(prod(intersect, x, y)))
)
nIntersections = Operator(
    "constructs intersection objects (of minimal cardinality) between object (line) regions",
    type=R2(Obj, Reg) ** R2(Obj, Reg) ** R2(Obj, Reg),
    body=lambda x, y: groupby (merge) (groupbyL (objectfromobjects) (select (compose (notj) (leq)) (prod3(apply1 (groupby (count)) (prod_3 (consIntersect (x, y))))) (Source(Count))))
)
nbuild = Operator(
    "build a network from objects with impedance values",
    type=ObjectInfo(Ratio) ** R3(Obj, Ratio, Obj)
)
nDist = Operator(
    "compute network distances between objects",
    type=(R2(Obj, Reg) ** R2(Obj, Reg)
          ** R3(Obj, Ratio, Obj) ** R3(Obj, Ratio, Obj))
)
nRoutes = Operator(
    "compute network routes (with distances) between objects",
    type=(R2(Obj, Reg) ** R2(Obj, Reg)
          ** R3(Obj, Ratio, Obj) ** R3(Obj, Reg, Obj))
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
    type=lambda x, y:
        (R2(Val, x) ** y) ** R2(Loc, x) ** Reg ** y [x < Qlt, y < Qlt],
    body=lambda f, x, r: f(subset(x, deify(r)))
)
ocont = Operator(
    "counts the number of objects within a region",
    type=R2(Obj, Reg) ** Reg ** Count,
    body=lambda x, y: get(pi2(
        groupbyR(count, select(eq, orTopo(x, nest(y)), in_))
    ))
)
fcover = Operator(
    "measures the spatial coverage of a field that is constrained to certain "
    "field values",
    type=lambda x: R2(Loc, x) ** R1(x) ** R1(Loc) [x < Qlt],
    body=lambda x, y: pi1(subset(x, y))
)
ocover = Operator(
    "measures the spatial coverage of a collection of objects",
    type=R2(Obj, Reg) ** R1(Obj) ** Reg,
    body=lambda x, y: merge(pi2(subset(x, y)))
)

# Functional and relational transformations ###############################

# Functional operators

compose = Operator(
    "compose unary functions",
    type=lambda α, β, γ: (β ** γ) ** (α ** β) ** (α ** γ),
    body=lambda f, g, x: f(g(x))
)
compose2 = Operator(
    "compose binary functions",
    type=lambda α, β, γ, δ: (β ** γ) ** (δ ** α ** β) ** (δ ** α ** γ),
    body=lambda f, g, x, y: f(g(x, y))
)
swap = Operator(
    "swap binary function inputs",
    type=lambda α, β, γ: (α ** β ** γ) ** (β ** α ** γ),
    body=lambda f, x, y: f(y, x)
)
id_ = Operator(
    "identity",
    type=lambda α: α ** α,
    body=lambda x: x
)
apply = Operator(
    "applying a function to a collection",
    type=lambda x, y: (x ** y) ** R1(x) ** R2(x, y)
)

# Set operations

# This should be a single operator, nest: R(x, y)
addlist=Operator(
    "construct a list",
    type=lambda x: List(x) ** x ** List(x)
)
emptylist = Operator(
    "empty list",
    type=lambda x:List(x)
)
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
consTuple = Operator(
    "put values in ternary relation",
    type=lambda x, y, z: R2(x, y) ** R2(x, z)** R2(x, y * z)
)
# There should be an empty relation operator
# This should have both key and value, and the relation should come last
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
    body=lambda x, y: relunion(add(nest(x), y))
)
set_diff = Operator(
    "difference of two relations",
    type=lambda rel: rel ** rel ** rel
)
set_inters = Operator(
    "intersection of two relations",
    type=lambda rel: rel ** rel ** rel,
    body=lambda x, y: set_diff(x, set_diff(x, y))
)
relunion = Operator(
    "union of a set of relations",
    type=lambda rel: R1(rel) ** rel [rel << {R1(_), R2(_, _), R3(_, _, _)}]
)
prod = Operator(
    "A constructor for quantified relations. Prod generates a cartesian "
    "product of two relations as a nested binary relation.",
    type=lambda x, y, z, u, w:
        (y ** z ** u) ** R2(x, y) ** R2(w, z) ** R2(x, R2(w, u)),
    body=lambda f, x, y: apply1(compose(swap(apply1, y), f), x)
)
prod3 = Operator(
    doc=("prod3 generates a quantified relation from two nested binary "
         "relations. The keys of the nested relations become two keys of "
         "the quantified relation."),
    type=lambda x, y, z: R2(z, R2(x, y)) ** R3(x, y, z),
)
prod_3 = Operator(
    doc=("prod_3 is the inverse of prod3."),
    type=lambda x, y, z: R3(x, y, z) ** R2(z, R2(x, y)),
)

# Projection (π)

pi1 = Operator(
    "projects a given relation to the first attribute, resulting in a "
    "collection",
    type=lambda rel, x: rel ** R1(x) [with_param(rel, x, at=1)]
)
pi2 = Operator(
    "projects a given relation to the second attribute, resulting in a "
    "collection",
    type=lambda rel, x: rel ** R1(x) [with_param(rel, x, at=2)],
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
        (x ** y ** Bool) ** rel ** y ** rel [with_param(rel, x)]
)
subset = Operator(
    "Subset a relation to those tuples having an attribute value contained in "
    "a collection",
    type=lambda x, rel: rel ** R1(x) ** rel [with_param(rel, x)],
    body=lambda r, c: select(inrel, r, c)
)

select2 = Operator(
    "Selects a subset of a relation using a constraint on two attributes, "
    "like equality (eq) or order (leq)",
    type=lambda x, y, rel:
        (x ** y ** Bool) ** rel ** rel [with_param(rel, y), with_param(rel, x)]
)

# remove nest
# empty: R(x, y)
# keys: R(x, y) -> R(x, ())
# values: R(x, y) -> R(y, ())
# map: (y -> z) -> R(x, y) -> R(x, z)
# left: x * _ -> x
# right: _ * x -> x

# Join (⨝)
join = Operator(
    "Join of two unary concepts, like a table join",
    type=lambda x, y, z: R2(x, y) ** R2(y, z) ** R2(x, z)
)

# functions to handle multiple attributes (with 1 key)
join_attr = Operator(
    type=lambda x, y, z: R2(x, y) ** R2(x, z) ** R2(x, y * z),
    # body=lambda x1, x2: prod3(pi12(select2(
    #     eq,
    #     prod3(apply1(compose(swap(apply1, x1), nest2), x2))
    # )))
)
get_attrL = Operator(
    type=lambda x, y, z: R2(x, y * z) ** R2(x, y),
    body=None
)
get_attrR = Operator(
    type=lambda x, y, z: R2(x, y * z) ** R2(x, z),
    body=None
)

join_key = Operator(
    "Substitute the quality of a quantified relation to some quality of one "
    "of its keys.",
    type=lambda x, q1, y, rel, q2:
        R3(x, q1, y) ** rel ** R3(x, q2, y) [rel << {R2(x, q2), R2(y, q2)}],
    # body=lambda x, y: prod3(apply1(subset(y), groupbyL(pi1, x)))
)

apply1 = Operator(
    "Join with unary function. Generates a unary concept from one other "
    "unary concept using a function",
    type=lambda x1, x2, y:
        (x1 ** x2) ** R2(y, x1) ** R2(y, x2),
    body=lambda f, y: join(y, apply(f, pi2(y)))
)
apply2 = Operator(
    "Join with binary function. Generates a unary concept from two other "
    "unary concepts of the same type",
    type=lambda x1, x2, x3, y:
        (x1 ** x2 ** x3) ** R2(y, x1) ** R2(y, x2) ** R2(y, x3),
    body=lambda f, x, y: pi12(select2(eq, prod3(prod(f, x, y))))
)

groupbyL = Operator(
    "Group quantified relations by the left key, summarizing lists of "
    "quality values with the same key value into a new value per key, "
    "resulting in a unary concept.",
    type=lambda rel, l, q1, q2, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(l, q2) [rel << {R1(r), R2(r, q1)}],
)
groupbyR = Operator(
    "Group quantified relations by the right key, summarizing lists of "
    "quality values with the same key value into a new value per key, "
    "resulting in a unary concept.",
    type=lambda rel, q2, l, q1, r:
        (rel ** q2) ** R3(l, q1, r) ** R2(r, q2) [rel << {R1(l), R2(l, q1)}]
)
groupby = Operator(
    "Group by qualities of binary relations",
    type=lambda l, q, y:
        (R1(l) ** q) ** R2(l, y) ** R2(y, q),
)

# Language ###################################################################

cct = Language(
    scope=locals(),
    namespace=("cct", "https://quangis.github.io/vocab/cct#"),
    canon={
        Top,
        Val,
        R1(Val),
        R2(Reg, Qlt),
        R2(Qlt, Reg),
        R2(Qlt, Qlt),
        R2(Obj, Reg),
        R2(Obj, Qlt),
        R2(Loc, Qlt),
        R2(Obj, Reg * Qlt),
        R3(Obj, Qlt, Obj),
        R3(Loc, Qlt, Obj),
        R3(Loc, Qlt, Loc),
        R3(Obj, Reg, Obj)
    })
CCT = cct.namespace
