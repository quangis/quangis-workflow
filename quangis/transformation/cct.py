"""
Module containing the core concept transformation algebra.
"""

from itertools import chain
from typing import List

from quangis.transformation.type import TypeOperator, TypeVar, AlgebraType
from quangis.transformation.algebra import TransformationAlgebra


def has(t: AlgebraType, at=None) -> List[AlgebraType]:
    """
    Typeclass for relationship types that contain another type somewhere.
    """
    R = TypeOperator.R
    if at == 1:
        return [R(t), R(t, TypeVar()), R(t, TypeVar(), TypeVar())]
    elif at == 2:
        return [R(TypeVar(), t), R(TypeVar(), t, TypeVar())]
    elif at == 3:
        return [R(TypeVar(), TypeVar(), t)]
    return list(chain(*(has(t, at=i) for i in range(1, 4))))


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

    ##########################################################################
    # Types and type synonyms

    Ent = TypeOperator("Ent")
    Obj = TypeOperator("Obj", supertype=Ent)  # O
    Reg = TypeOperator("Reg", supertype=Ent)  # S
    Loc = TypeOperator("Loc", supertype=Ent)  # L
    Qlt = TypeOperator("Qlt", supertype=Ent)  # Q
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
    object = R(Obj), 1
    region = R(Reg), 1
    in_ = Nom, 0
    countV = Count, 1
    ratioV = Ratio, 1
    interval = Itv, 1
    ordinal = Ord, 1
    nominal = Nom, 1

    ##########################################################################
    # Geographic transformations

    # functional
    compose = (y ** z) ** (x ** y) ** (x ** z)

    # derivations
    ratio = Ratio ** Ratio ** Ratio

    # aggregations of collections
    count = R(Obj) ** Ratio
    size = R(Loc) ** Ratio
    merge = R(Reg) ** Reg
    centroid = R(Loc) ** Loc

    # statistical operations
    avg = R(Ent, Itv) ** Itv
    min = R(Ent, Ord) ** Ord
    max = R(Ent, Ord) ** Ord
    sum = R(Ent, Count) ** Count

    ##########################################################################
    # Geographic transformations

    # conversions
    reify = R(Loc) ** Reg
    deify = Reg ** R(Loc)
    get = R(x) ** x, x << [Ent]
    invert = x ** y, x ** y << [R(Loc, Ord) ** R(Ord, Reg), R(Loc, Nom) ** R(Reg, Nom)]
    revert = x ** y, x ** y << [R(Ord, Reg) ** R(Loc, Ord), R(Reg, Nom) ** R(Loc, Nom)]

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
    pi1 = x ** y, x << has(y, at=1)
    pi2 = x ** y, x << has(y, at=2)
    pi3 = x ** y, x << has(y, at=3)

    # selection operations
    sigmae = x ** y ** x, x << [Qlt], y << has(x)
    sigmale = x ** y ** x, x << [Ord], y << has(x)

    # join and set operations
    bowtie = x ** R(y) ** x, y << [Ent], y << has(x)
    bowtiestar = R(x, y, x) ** R(x, y) ** R(x, y, x), y << [Qlt], x << [Ent]
    bowtie_ = (Qlt ** Qlt ** Qlt) ** R(Ent, Qlt) ** R(Ent, Qlt) ** R(Ent, Qlt)

    # group by
    groupbyL = (R(y, Qlt) ** Qlt) ** R(x, Qlt, y) ** R(x, Qlt), x << [Ent], y << [Ent]
    groupbyR = (R(x, Qlt) ** Qlt) ** R(x, Qlt, y) ** R(y, Qlt), x << [Ent], y << [Ent]
    groupbyR_simpler = (R(Ent) ** z) ** R(x, Qlt, y) ** R(y, z)
