import unittest

from quangis import error
from quangis.transformation.cct import cct, \
    R1, R2, Obj, Ratio, Itv, Count, Reg, Loc, Ord, Nom


class TestCCT(unittest.TestCase):

    def parse(self, string, result):
        if isinstance(result, type) and issubclass(result, Exception):
            self.assertRaises(result, cct.parse, string)
        else:
            self.assertEqual(cct.parse(string).type, result)

    @unittest.skip("this would be desirable")
    def test_projection(self):
        self.parse(
            "pi1 (objectregions xs)",
            R1(Obj))

    def test_select_match(self):
        self.parse(
            "select eq (objects xs) (object x)",
            R2(Obj, Ratio))

    def test_select_mismatch(self):
        self.parse(
            "select eq (objects xs) (region x)",
            error.ViolatedConstraint)

    def test01(self):
        self.parse(
            "compose deify reify (pi1 (field something))",
            R1(Loc))

    def test02(self):
        self.parse(
            "select eq (objectregions x) (object y)",
            R2(Obj, Reg))

    def test03(self):
        self.parse(
            "select eq (amountpatches x) (nominal y)",
            R2(Reg, Nom))

    def test04(self):
        self.parse(
            "select leq (contour x) (ordinal y)",
            R2(Ord, Reg))

    def test05(self):
        self.parse(
            "join_subset (objectregions x) (pi1 (select eq (otopo "
            "(objectregions x) (objectregions y)) in))",
            R2(Obj, Reg))

    def test06(self):
        self.parse(
            "groupbyL sum (join_key (select eq (otopo (objectregions x) "
            "(objectregions y)) in) (objectcounts z))",
            R2(Obj, Count))

    def test07(self):
        self.parse(
            "groupbyL sum (join_key (select eq (otopo (objectregions x) "
            "(objectregions y)) in) (objects z))",
            R2(Obj, Count))

    def test08(self):
        self.parse(
            "groupbyL avg (join_key (select eq (otopo (objectregions x) "
            "(objectregions y)) in) (objects z))",
            R2(Obj, Itv))

    def test09(self):
        self.parse(
            "groupbyL avg (join_key (select eq (otopo (objectregions x) "
            "(objectregions y)) in) (objectcounts z))",
            R2(Obj, Itv))

    def test10(self):
        self.parse(
            "groupbyR count (select eq (otopo (objectregions x) "
            "(objectregions y)) in)",
            R2(Obj, Ratio))

    def test11(self):
        self.parse(
            "revert2 (contour x)",
            R2(Loc, Ord))

    def test12(self):
        self.parse(
            "revert (amountpatches x)",
            R2(Loc, Nom))

    def test13(self):
        self.parse(
            "invert (field x)",
            R2(Reg, Ratio))

    def test14(self):
        self.parse(
            "select leq (field x) (ordinal y)",
            R2(Loc, Ratio))

    def test15(self):
        self.parse(
            "groupbyR size (select eq (lotopo (pi1 (field x))"
            "(objectregions y)) in)",
            R2(Obj, Ratio))

    def test16(self):
        self.parse(
            "groupbyR size (select eq (lotopo (deify (merge (pi2 "
            "(objectregions x)))) (objectregions x)) in)",
            R2(Obj, Ratio))

    def test17(self):
        self.parse(
            "join_with2 ratio (objects x) (objects y)",
            R2(Obj, Ratio))

    def test18(self):
        self.parse(
            "interpol (pointmeasures x) "
            "(deify (merge (pi2 (objectregions y))))",
            R2(Loc, Itv))

    def test19(self):
        self.parse(
            "groupbyL avg (join_key (select eq (lotopo (pi1 (field x)) "
            "(objectregions y)) in) (field b))",
            R2(Loc, Itv))

    def test20(self):
        self.parse(
            "join_subset (field x) (deify (merge (pi2 (objectregions x))))",
            R2(Loc, Ratio))

    def test21(self):
        self.parse(
            "reify (pi1 (field x))",
            Reg)

    def test22(self):
        self.parse(
            "groupbyR count (select eq (otopo (objectregions _:source3) "
            "(join_subset (objectregions _:source2) (pi1 (select eq (otopo "
            "(objectregions _:source2) (select eq (objectregions _:source1)"
            "(object Amsterdam))) in)))) in)",
            R2(Obj, Ratio))

    def test23(self):
        self.parse(
            "join_subset (objectregions roads) (pi3 (select eq (lotopo (deify "
            "(region 1234)) (objectregions roads)) in))",
            R2(Obj, Reg))

    def test24(self):
        self.parse(
            "reify (pi1 (select leq (join_subset (revert2 (contour noise)) "
            "(deify (merge (pi2 (select eq (objectregions muni) "
            "(object Utrecht)))))) (ordinal 70)))",
            Reg)

    def test25(self):
        self.parse(
            "join_with2 ratio (groupbyR size (select eq (lotopo (pi1 (select "
            "leq (revert2 (contour noise)) (ordinal 70))) (select eq "
            "(objectregions muni) (object Utrecht))) in)) (groupbyR size "
            "(select eq (lotopo (deify (merge (pi2 (objectregions muni)))) "
            "(select eq (objectregions muni) (object Utrecht))) in))",
            R2(Obj, Ratio))

    def test26(self):
        self.parse(
            "groupbyR sum (join_key (select eq (otopo (objectregions "
            "households) (join_subset (objectregions neighborhoods) (pi1 "
            "(select eq (otopo (objectregions neighborhoods) (select eq "
            "(objectregions muni) (object Utrecht))) in)))) in) "
            "(objectcounts households))",
            R2(Obj, Count))

    def test27(self):
        self.parse(
            "groupbyR avg (join_key (select eq (lotopo (deify (merge (pi2 "
            "(select eq (objectregions muni) (object Utrecht))))) "
            "(join_subset (objectregions neighborhoods) (pi1 (select eq "
            "(otopo (objectregions neighborhoods) (select eq (objectregions "
            "muni) (object Utrecht))) in)))) in) (interpol (pointmeasures "
            "temperature) (deify (merge (pi2 (select eq (objectregions muni) "
            "(object Utrecht)))))))",
            R2(Obj, Itv))

    def test28(self):
        self.parse(
            "ratio (fcont (interpol (pointmeasures temperature) (deify (merge "
            "(pi2 (select eq (objectregions muni) (object Utrecht))))))) (size"
            "(pi1 (interpol (pointmeasures temperature) (deify (merge (pi2 "
            "(select eq (objectregions muni) (object Utrecht))))))))",
            Ratio)


if __name__ == '__main__':
    unittest.main()
