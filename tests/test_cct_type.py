import unittest

from quangis import error
from quangis.transformation.type import TypeOperator, TypeVar, Constraint
from quangis.transformation.algebra import TransformationAlgebra

Any = TypeOperator.Any()
Int = TypeOperator.Int(supertype=Any)
Str = TypeOperator.Str(supertype=Any)
T = TypeOperator.T


def var(n):
    for _ in range(0, n):
        yield TypeVar()


class A(TransformationAlgebra):

    x, y, z = TypeVar(), TypeVar(), TypeVar()

    compose = ((y ** z) ** (x ** y) ** (x ** z))
    id_any = x ** x, Constraint(x, Any)
    id_int = x ** x, Constraint(x, Int)
    id_spec = x ** x, Constraint(x, Int, Str)


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
        x, y = var(2)
        self.assertEqual((x ** y).apply(x), y)

        x, y = var(2)
        self.assertEqual((Int ** y).apply(x), y)

        x, y = var(2)
        self.assertEqual((x ** y).apply(Int), y)

        x, y = var(2)
        self.assertEqual((x ** x).apply(Int), Int)

        x, y = var(2)
        self.assertEqual((T(x) ** x).apply(T(Int)), Int)

        x, y = var(2)
        self.assertEqual((x ** T(x)).apply(Int), T(Int))

    def test_apply_recursive_type(self):
        x = TypeVar()
        self.assertRaises(error.RecursiveType, ((x ** x) ** Int).apply, x)

    def test_compose_concrete(self):
        self.assertEqual(
            A.compose.instance().apply(Int ** Str).apply(Str ** Int),
            Str ** Str)

    def test_compose_variable(self):
        x = TypeVar()
        self.assertEqual(
            A.compose.instance().apply(x ** Str).apply(Int ** x), Int ** Str)

    def test_simple_subtypes(self):
        self.assertEqual((Any ** Any).apply(Int), Any)
        self.assertRaises(error.TypeMismatch, (Int ** Any).apply, Any)

    def test_complex_subtypes(self):
        self.assertEqual((T(Any) ** Any).apply(T(Int)), Any)
        self.assertRaises(error.TypeMismatch, (T(Int) ** Any).apply, T(Any))

    def test_complex_variable_subtypes(self):
        x = TypeVar()
        self.assertEqual((T(Any, x) ** x).apply(T(Int, Any)), Any)

        x = TypeVar()
        self.assertRaises(error.TypeMismatch, (T(Int, x) ** x).apply, T(Any, Any))

    def test_simple_constraints(self):
        func = A.id_int.instance()
        self.assertEqual(func.apply(Int), Int)
        self.assertRaises(error.TypeMismatch, func.apply, Str)

    def test_subtyping_on_constraints(self):
        func = A.id_any.instance()
        self.assertEqual(func.apply(Str), Str)

    def test_multiple_constraints(self):
        func = A.id_spec.instance()
        self.assertEqual(func.apply(Str), Str)
        func = A.id_spec.instance()
        self.assertEqual(func.apply(Int), Int)
        func = A.id_spec.instance()
        self.assertRaises(error.TypeMismatch, func.apply, Any)

#    @unittest.skip("should constraints unify?")
#    def test_constraint_on_input_variable(self):
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** (y ** Str))).instance()
#        self.assertEqual(func.apply(T(Int, Str)).apply(Str), Str)
#
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("test", (x ** (y ** Str))).instance()
#        self.assertEqual(func.apply(T(Int, Str)).apply(Int), Str)
#
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** (y ** Str), x << [T(Int, y)])).instance()
#        self.assertEqual(func.apply(T(Int, Str)).apply(Str), Str)
#
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** (y ** Str), x << [T(Int, y)])).instance()
#        self.assertRaises(RuntimeError, func.apply(T(Int, Str)).apply, Int)
#
#    def test_complex_constraint_subject(self):
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** y, x ** y << [Int ** Str])).instance()
#        self.assertRaises(RuntimeError, func.apply, Str)
#
#    @unittest.skip("should constraints unify?")
#    def test_unify_constraint_if_only_one_possibility(self):
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** y, x ** y << [Int ** Str])).instance()
#        self.assertEqual(func.apply(Int), Str)
#
#    def test_constraint_without_variables(self):
#        self.assertRaises(RuntimeError, Int.__lshift__, [Int])
#
#    def test_recursive_constraint(self):
#        x = TypeVar()
#        self.assertRaises(RuntimeError, x.__lshift__, [Int ** x])
#
#    @unittest.skip("should constraints unify?")
#    def test_constraint_is_bound_on_subject_side(self):
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (x ** y, x << [y])).instance()
#        self.assertEqual(func.apply(Int), Int)
#
#    @unittest.skip("should constraints unify?")
#    def test_constraint_is_bound_on_typeclass_side(self):
#        # It won't work immediately, but the constraint will hold once the
#        # other variable is bound
#        x, y = TypeVar(), TypeVar()
#        func = Definition.from_tuple("t", (y ** x ** Str, x << [y])).instance()
#        self.assertEqual(func.apply(Int).apply(Int), Str)
#        self.assertRaises(RuntimeError, func.apply(Int).apply, Str)


if __name__ == '__main__':
    unittest.main()
