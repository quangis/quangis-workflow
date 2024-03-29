import unittest

from quangis.namespace import EX
from quangis.polytype import Polytype, Dimension


class TestPolytype(unittest.TestCase):

    def assertSubtype(self, *expected: tuple[Polytype, Polytype, bool]):
        for a, b, value in expected:
            with self.subTest(f"{a} <= {b}"):
                self.assertEqual(Polytype.subtype(a, b), value)

    def test_subtypes(self):
        dim = Dimension(EX.A, {EX.A: [EX.B, EX.C], EX.B: [EX.D], EX.C: [EX.D]})
        t1 = Polytype({dim: [EX.A]})
        t2 = Polytype({dim: [EX.B, EX.C]})
        t3 = Polytype({dim: [EX.D]})

        # t2 <= t2 is interesting: B & C is not a subtype of itself because B 
        # is not a subtype of C (or vice versa). Is this correct? TODO
        self.assertSubtype(
            (t1, t1, True), (t1, t2, False), (t1, t3, False),
            (t2, t1, True), (t2, t2, False), (t2, t3, False),
            (t3, t1, True), (t3, t2, True), (t3, t3, True),
        )

    def test_subtypes_partial(self):
        # Subtype relations are partial, not total.
        dim = Dimension(EX.A, {EX.A: [EX.B, EX.C]})
        t1 = Polytype({dim: [EX.B]})
        t2 = Polytype({dim: [EX.C]})
        self.assertSubtype((t1, t2, False), (t1, t2, False))

    def test_subtypes_intersecting(self):
        # The types are interwoven here in such a way that t1 cannot be a 
        # subtype of t2 because B is not a subtype of C, and t2 cannot be a 
        # subtype of t1 because E is not a subtype of C or D (and C is not a 
        # subtype of D). The set of types is a conjunction!
        dim = Dimension(EX.A, {
            EX.A: [EX.B, EX.C],
            EX.B: [EX.D, EX.E],
            EX.C: [EX.D]})
        t1 = Polytype({dim: [EX.B, EX.D]})
        t2 = Polytype({dim: [EX.C, EX.E]})
        self.assertSubtype((t1, t2, False), (t1, t2, False))

    def test_normalization(self):
        """Polytypes need to be normalizable so that they can be sortable."""
        dim = Dimension(EX.A, {
            EX.A: [EX.B, EX.C],
            EX.B: [EX.D, EX.E],
            EX.C: [EX.D]})

        self.assertEqual(
            Polytype({dim: [EX.E, EX.D]}).normalize(),
            Polytype({dim: [EX.E, EX.D]})
        )

        self.assertNotEqual(
            Polytype({dim: [EX.B, EX.D]}).normalize(),
            Polytype({dim: [EX.B, EX.D]})
        )
        self.assertEqual(
            Polytype({dim: [EX.B, EX.D]}).normalize(),
            Polytype({dim: [EX.D]})
        )
        self.assertEqual(
            Polytype({dim: [EX.A, EX.D]}).normalize(),
            Polytype({dim: [EX.D]})
        )
        self.assertEqual(
            Polytype({dim: [EX.B, EX.C]}).normalize(),
            Polytype({dim: [EX.B, EX.C]})
        )
        self.assertEqual(
            Polytype({dim: [EX.B, EX.C, EX.D]}).normalize(),
            Polytype({dim: [EX.D]})
        )

    def test_sorted(self):
        """Polytypes need to be sortable."""
        # This was originally implemented so that permutations of inputs can
        # be detected, but I forgot about subtypes, so this and 
        # `Polytype.lexical` can probably be removed later on.

        dim1 = Dimension(EX.A, {
            EX.A: [EX.B, EX.C],
            EX.C: [EX.D],
            EX.B: [EX.D, EX.E]})
        dim2 = Dimension(EX.F, {
            EX.F: [EX.B],
            EX.B: [EX.C]})

        self.assertGreater(
            Polytype({dim1: [EX.A, EX.D]}).lexical(),
            Polytype({dim1: [EX.A, EX.C]}).lexical()
        )
        self.assertLess(
            Polytype({dim1: [EX.D]}).lexical(),
            Polytype({dim1: [EX.E]}).lexical()
        )
        self.assertEqual(
            Polytype({dim1: [EX.A, EX.D]}).lexical(),
            Polytype({dim1: [EX.C, EX.D]}).lexical()
        )

        self.assertGreater(
            Polytype({
                dim1: [EX.A, EX.D],
                dim2: [EX.C]
            }).lexical(),
            Polytype({
                dim1: [EX.A, EX.C],
                dim2: [EX.B]
            }).lexical()
        )


if __name__ == '__main__':
    unittest.main()
