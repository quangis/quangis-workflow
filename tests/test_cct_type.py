import unittest
from functools import partial

from quangis.cct.type import TypeOperator, TypeVar

x, y, z = TypeVar.new(), TypeVar.new(), TypeVar.new()
Int = TypeOperator("int")
Str = TypeOperator("str")
T = partial(TypeOperator, "T")
compose = ((y ** z) ** (x ** y) ** (x ** z)).fresh()


class TestType(unittest.TestCase):

    def test_apply_non_function(self):
        self.assertRaises(RuntimeError, Int.apply, Int)

    def test_apply_simple_function(self):
        self.assertEqual((Int ** Str).apply(Int), Str)
        self.assertRaises(RuntimeError, (Str ** Int).apply, Int)

    def test_apply_complex_function(self):
        self.assertEqual((T(Int) ** T(Str)).apply(T(Int)), T(Str))
        self.assertRaises(RuntimeError, (Int ** Int).apply, T(Int))

    def test_apply_variable_function(self):
        self.assertEqual((x ** y).apply(x), y)
        self.assertEqual((Int ** y).apply(x), y)
        self.assertEqual((x ** y).apply(Int), y)
        self.assertEqual((x ** x).apply(Int), Int)
        self.assertEqual((T(x) ** x).apply(T(Int)), Int)
        self.assertEqual((x ** T(x)).apply(Int), T(Int))

    def test_apply_recursive_type(self):
        self.assertRaises(RuntimeError, ((x ** x) ** Int).apply, x)

    def test_compose_concrete(self):
        self.assertEqual(compose.apply(Int ** Str).apply(Str ** Int), Str ** Str)

    def test_compose_variable(self):
        print()
        print(compose)
        print(compose.apply(x ** Str))
        self.assertEqual(compose.apply(x ** Str).apply(Int ** x), Int ** Str)


if __name__ == '__main__':
    unittest.main()
