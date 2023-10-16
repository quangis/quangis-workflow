"""This module is an attempt at converting CCT types to (incomplete) CCD 
types."""

from quangis.ccd import CCD, ccd
from quangis.cct import cct, R3
from quangis.polytype import Polytype
from rdflib import URIRef
from transforge.type import TypeOperation, Product

# Conversion from CCT to CCD as made by Simon
conversion = {
    "R(_,Count)": {CCD.NominalA: [CCD.CountA]},
    "Reg": {CCD.LayerA: [CCD.RegionA]},
    "C(Loc)": {CCD.LayerA: [CCD.RegionA]},
    "R(_,Itv)": {CCD.NominalA: [CCD.IntervalA]},
    "R(Loc,Bool)": {CCD.CoreConceptQ: [CCD.FieldQ], CCD.NominalA: [CCD.BooleanA]},
    "R(Loc,Itv)": {CCD.CoreConceptQ: [CCD.FieldQ], CCD.NominalA: [CCD.IntervalA]},
    "R(Loc,Nom)": {CCD.CoreConceptQ: [CCD.FieldQ], CCD.NominalA: [CCD.NominalA]},
    "R(Loc,Ord)": {CCD.CoreConceptQ: [CCD.FieldQ], CCD.NominalA: [CCD.OrdinalA]},
    "R(Loc,Ratio)": {CCD.CoreConceptQ: [CCD.FieldQ], CCD.NominalA: [CCD.RatioA]},
    "R(_,Nom)": {CCD.NominalA: [CCD.NominalA]},
    "R(Obj,_)": {CCD.CoreConceptQ: [CCD.ObjectQ]},
    "R(Obj*Obj,Itv)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.IntervalA]},
    "R(Obj*Obj,Nom)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.NominalA]},
    "R(Obj*Obj,Ord)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.OrdinalA]},
    "R(Obj*Obj,Ratio)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.RatioA]},
    "R(Obj*Obj,Reg)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.LayerA: [CCD.LineA]},
    "R(Obj,Reg)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Top)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Bool)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.BooleanA], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Count)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.CountA], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Itv)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.IntervalA], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Nom)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.NominalA], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Ord)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.OrdinalA], CCD.LayerA: [CCD.VectorA]},
    "R(Obj,Reg*Ratio)": {CCD.CoreConceptQ: [CCD.ObjectQ], CCD.NominalA: [CCD.RatioA], CCD.LayerA: [CCD.VectorA]},
    "R(_,Ord)": {CCD.NominalA: [CCD.OrdinalA]},
    "R(_,Ratio)": {CCD.NominalA: [CCD.RatioA]},
    "R(_,Reg)": {CCD.LayerA: [CCD.VectorA]},
    "R(Reg,_)": {CCD.LayerA: [CCD.VectorA]},
    "R(Reg,Count)": {CCD.NominalA: [CCD.CountA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg,Itv)": {CCD.NominalA: [CCD.CountA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg,Nom)": {CCD.NominalA: [CCD.CountA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg*Obj,Itv)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.CountA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg*Obj,Nom)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.NominalA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg*Obj,Ord)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.OrdinalA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg*Obj,Ratio)": {CCD.CoreConceptQ: [CCD.NetworkQ], CCD.NominalA: [CCD.RatioA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg,Ord)": {CCD.NominalA: [CCD.OrdinalA], CCD.LayerA: [CCD.VectorA]},
    "R(Reg,Ratio)": {CCD.NominalA: [CCD.RatioA], CCD.LayerA: [CCD.VectorA]},
}


def cct2ccd(uri: URIRef) -> Polytype:
    t2 = cct.parse_type_uri(uri)
    dims = {d.root: d for d in ccd.dimensions}
    for k, v in conversion.items():
        t = cct.parse_type(k)

        # This is a temporary solution: R(x * z, y) is for now
        # converted to the old-style R3(x, y, z)
        if t.params and isinstance(t.params[0], TypeOperation) and \
                t.params[0].operator == Product:
            t = R3(t.params[0].params[0], t.params[1], t.params[0].params[1])

        if t.match(t2, accept_wildcard=True) is not False:
            return Polytype({dims[d]: uris for d, uris in v.items()})
    raise RuntimeError(f"Cannot convert CCT type {uri} to CCD.")
