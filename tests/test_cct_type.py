import unittest
from functools import partial

from quangis.transformation.type import TypeOperator, TypeVar

x, y, z = TypeVar(), TypeVar(), TypeVar()
Any = TypeOperator("any")
Int = TypeOperator("int", supertype=Any)
Str = TypeOperator("str", supertype=Any)
T = partial(TypeOperator, "T")

def new_vars(n):
    for i in range(0, n):
        yield TypeVar()


def compose():
    x, y, z = TypeVar(), TypeVar(), TypeVar()
    return ((y ** z) ** (x ** y) ** (x ** z))


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
        x, y = new_vars(2)
        self.assertEqual((x ** y).apply(x), y)
        x, y = new_vars(2)
        self.assertEqual((Int ** y).apply(x), y)
        x, y = new_vars(2)
        self.assertEqual((x ** y).apply(Int), y)
        x, y = new_vars(2)
        self.assertEqual((x ** x).apply(Int), Int)
        x, y = new_vars(2)
        self.assertEqual((T(x) ** x).apply(T(Int)), Int)
        x, y = new_vars(2)
        self.assertEqual((x ** T(x)).apply(Int), T(Int))

    def test_apply_recursive_type(self):
        self.assertRaises(RuntimeError, ((x ** x) ** Int).apply, x)

    def test_compose_concrete(self):
        self.assertEqual(compose().apply(Int ** Str).apply(Str ** Int), Str ** Str)

    def test_compose_variable(self):
        x = TypeVar()
        self.assertEqual(compose().apply(x ** Str).apply(Int ** x), Int ** Str)

    def test_simple_subtypes(self):
        self.assertEqual((Any ** Any).apply(Int), Any)
        self.assertRaises(RuntimeError, (Int ** Any).apply, Any)

    def test_complex_subtypes(self):
        self.assertEqual((T(Any) ** Any).apply(T(Int)), Any)
        self.assertRaises(RuntimeError, (T(Int) ** Any).apply, T(Any))

    def test_complex_variable_subtypes(self):
        self.assertEqual((T(Any, x) ** x).apply(T(Int, Any)), Any)
        self.assertRaises(RuntimeError, (T(Int, x) ** x).apply, T(Any, Any))


class TestSubtypes(unittest.TestCase):

    def test_subclasses(self):
        self.assertTrue(Int.subtype(Int))
        self.assertTrue(Int.subtype(Any))
        self.assertFalse(Any.subtype(Int))


if __name__ == '__main__':
    unittest.main()
