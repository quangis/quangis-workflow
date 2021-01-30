"""
Module containing the core concept transformation algebra.
"""

from collections import defaultdict

from quangis.transformation.type import TypeOperator, TypeVar
from quangis.transformation.algebra import TransformationAlgebra


class CCT(TransformationAlgebra):
    """
    Core concept transformation algebra. Usage:

        >>> cct = CCT()
        >>> expr = cct.parse("pi1 (objects data)")
        >>> print(expr.type)
        R(Obj)

    """

    # Some type variables for convenience
    x, y, z = (TypeVar() for _ in range(0, 3))

    # Dispenser for generic variables
    v = defaultdict(TypeVar)
    rel, q = TypeVar(), TypeVar()

    ##########################################################################
    # Types and type synonyms

    Val = TypeOperator("Val")
    Obj = TypeOperator("Obj", supertype=Val)  # O
    Reg = TypeOperator("Reg", supertype=Val)  # S
    Loc = TypeOperator("Loc", supertype=Val)  # L
    Qlt = TypeOperator("Qlt", supertype=Val)  # Q
    Nom = TypeOperator("Nom", supertype=Qlt)
    Bool = TypeOperator("Bool", supertype=Nom)
    Ord = TypeOperator("Ord", supertype=Nom)
    Count = TypeOperator("Count", supertype=Ord)
    Ratio = TypeOperator("Ratio", supertype=Count)
    Itv = TypeOperator("Itv", supertype=Ratio)
    R = TypeOperator.R

    SpatialField = R(Loc, Qlt)
    InvertedField = R(Qlt, Reg)
    FieldSample = R(Reg, Qlt)
    ObjectExtent = R(Obj, Reg)
    ObjectQuality = R(Obj, Qlt)
    NominalField = R(Loc, Nom)
    BooleanField = R(Loc, Bool)
    NominalInvertedField = R(Nom, Reg)
    BooleanInvertedField = R(Bool, Reg)

    ##########################################################################
    # Data inputs

    pointmeasures = R(Reg, Itv), 1
    amountpatches = R(Reg, Nom), 1
    contour = R(Ord, Reg), 1
    objects = R(Obj, Ratio), 1
    objectregions = R(Obj, Reg), 1
    contourline = R(Itv, Reg), 1
    objectcounts = R(Obj, Count), 1
    field = R(Loc, Ratio), 1
    object = Obj, 1
    region = Reg, 1
    in_ = Nom, 0
    countV = Count, 1
    ratioV = Ratio, 1
    interval = Itv, 1
    ordinal = Ord, 1
    nominal = Nom, 1

    ##########################################################################
    # Math/stats transformations

    # functional
    compose = (y ** z) ** (x ** y) ** (x ** z)

    # derivations
    ratio = Ratio ** Ratio ** Ratio
    le = Ord ** Ord ** Bool
    eq = Qlt ** Qlt ** Bool

    # aggregations of collections
    count = R(Obj) ** Ratio
    size = R(Loc) ** Ratio
    merge = R(Reg) ** Reg
    centroid = R(Loc) ** Loc

    # statistical operations
    avg = R(Val, Itv) ** Itv
    min = R(Val, Ord) ** Ord
    max = R(Val, Ord) ** Ord
    sum = R(Val, Count) ** Count

    ##########################################################################
    # Geographic transformations

    # conversions
    reify = R(Loc) ** Reg
    deify = Reg ** R(Loc)
    get = R(x) ** x, \
        x.limit(Val)
    invert = x ** y, (x ** y).limit(
        R(Loc, Ord) ** R(Ord, Reg),
        R(Loc, Nom) ** R(Reg, Nom))
    revert = x ** y, (x ** y).limit(
        R(Ord, Reg) ** R(Loc, Ord),
        R(Reg, Nom) ** R(Loc, Nom))

    # quantified relations
    oDist = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Ratio, Obj)
    lDist = R(Loc) ** R(Loc) ** R(Loc, Ratio, Loc)
    loDist = R(Loc) ** R(Obj, Reg) ** R(Loc, Ratio, Obj)
    oTopo = R(Obj, Reg) ** R(Obj, Reg) ** R(Obj, Nom, Obj)
    loTopo = R(Loc) ** R(Obj, Reg) ** R(Loc, Nom, Obj)
    nDist = R(Obj) ** R(Obj) ** R(Obj, Ratio, Obj) ** R(Obj, Ratio, Obj)
    lVis = R(Loc) ** R(Loc) ** R(Loc, Itv) ** R(Loc, Bool, Loc)
    interpol = R(Reg, Itv) ** R(Loc) ** R(Loc, Itv)

    # amount operations
    fcont = R(Loc, Itv) ** Ratio
    ocont = R(Obj, Ratio) ** Ratio

    ##########################################################################
    # Relational transformations

    # projection
    pi1 = rel ** R(x), rel.has_param(R, x, at=1)
    pi2 = rel ** R(x), rel.has_param(R, x, at=2)
    pi3 = rel ** R(x), rel.has_param(R, x, at=3)

    # selection operations

    sigmae = rel ** q ** rel, \
        q.limit(Val), rel.has_param(R, q)

    sigmale = x ** y ** x, \
        x.limit(Ord), y.has_param(R, x)

    # join and set operations
    bowtie = x ** R(y) ** x, \
        y.limit(Val), y.has_param(R, x)
    bowtiestar = R(x, y, x) ** R(x, y) ** R(x, y, x), \
        x.limit(Qlt), y.has_param(R, x)
    bowtie_ = (Qlt ** Qlt ** Qlt) ** R(Val, Qlt) ** R(Val, Qlt) ** R(Val, Qlt)

    # group by
    groupbyL = (R(y, Qlt) ** Qlt) ** R(x, Qlt, y) ** R(x, Qlt), \
        x.limit(Val), y.limit(Val)
    groupbyR = (R(x, Qlt) ** Qlt) ** R(x, Qlt, y) ** R(y, Qlt), \
        x.limit(Val), y.limit(Val)
    groupbyR_simpler = (R(Val) ** z) ** R(x, Qlt, y) ** R(y, z)
