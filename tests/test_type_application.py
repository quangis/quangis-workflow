import unittest

from quangis import error
from quangis.transformation.type import Operator, Schema, Subtype

Any = Operator('Any')
Ord = Operator('Ord', supertype=Any)
Bool = Operator('Bool', supertype=Ord)
Str = Operator('Str', supertype=Ord)
Int = Operator('Int', supertype=Ord)
UInt = Operator('UInt', supertype=Int)
T = Operator('T', 1)


class TestType(unittest.TestCase):

    def apply(self, f, x, result=None):
        """
        Test the application of an argument to a function.
        """
        f = f.instance()
        x = x.instance()

        if isinstance(result, type) and issubclass(result, Exception):
            self.assertRaises(result,
                lambda x: f(x).resolve(),
                x.instance())
        else:
            actual = f(x).resolve(force=True).plain
            expected = result.instance().plain
            # self.assertEqual(type(actual), type(expected))
            self.assertEqual(actual, expected)
            # self.assertEqual(actual.subtype(expected), expected.subtype(actual))

    def test_apply_non_function(self):
        self.apply(Int.instance(), Int, error.NonFunctionApplication)

    def test_basic_match(self):
        f = Int ** Str
        self.apply(f, Int, Str)

    def test_basic_mismatch(self):
        f = Int ** Str
        self.apply(f, Str, error.SubtypeMismatch)

    def test_basic_sub_match(self):
        f = Any ** Str
        self.apply(f, Int, Str)

    def test_basic_sub_mismatch(self):
        f = Int ** Str
        self.apply(f, Any, error.SubtypeMismatch)

    def test_compound_match(self):
        f = T(Int) ** Str
        self.apply(f, T(Int), Str)

    def test_compound_mismatch(self):
        f = T(Int) ** Str
        self.apply(f, T(Str), error.SubtypeMismatch)

    def test_compound_sub_match(self):
        f = T(Any) ** Str
        self.apply(f, T(Int), Str)

    def test_compound_sub_mismatch(self):
        f = T(Int) ** Str
        self.apply(f, T(Any), error.SubtypeMismatch)

    def test_variable(self):
        wrap = Schema(lambda α: α ** T(α))
        self.apply(wrap, Int, T(Int))

    def test_compose(self):
        compose = Schema(lambda x, y, z: (y ** z) ** (x ** y) ** (x ** z))
        self.apply(
            compose(Int ** Str), Str ** Int,
            Str ** Str)

    def test_compose_subtype(self):
        compose = Schema(lambda x, y, z: (y ** z) ** (x ** y) ** (x ** z))
        self.apply(
            compose(Int ** Str), Str ** UInt,
            Str ** Str)

    def test_variable_subtype_match(self):
        f = Schema(lambda x: (x ** Any) ** x)
        self.apply(f, Int ** Int, Int)

    def test_variable_subtype_mismatch(self):
        f = Schema(lambda x: (x ** Int) ** x)
        self.apply(f, Int ** Any, error.SubtypeMismatch)

    def test_weird(self):
        swap = Schema(lambda α, β, γ: (α ** β ** γ) ** (β ** α ** γ))
        f = Int ** Int ** Int
        x = UInt
        self.apply(swap(f, x), x, Int)

    def test_functions_as_arguments(self):
        id = Schema(lambda x: x ** x)
        f = Int ** Int
        x = UInt
        self.apply(id(f), x, Int)

    def test_order_of_subtype_application(self):
        """
        This test is inspired by Traytel et al (2011).
        """
        leq = Schema(lambda α: α ** α ** Bool)
        self.apply(leq(UInt), Int, Bool)
        self.apply(leq(Int), UInt, Bool)
        self.apply(leq(Int), Bool, error.SubtypeMismatch)

    def test_order_of_subtype_application_with_constraints(self):
        leq = Schema(lambda α: α ** α ** Bool | Subtype(α, Ord))
        self.apply(leq(Int), UInt, Bool)
        self.apply(leq, Any, error.SubtypeMismatch)


if __name__ == '__main__':
    unittest.main()
