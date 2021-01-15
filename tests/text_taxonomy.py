import unittest

from quangis import error
from quangis.namespace import TEST
from quangis.ontology import Taxonomy


class TestTaxonomy(unittest.TestCase):

    def test_multiple_children(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.a, TEST.c)
        self.assertEqual(set(t.children(TEST.a)), {TEST.b, TEST.c})

    def test_successive_children(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.b, TEST.c)
        self.assertEqual(set(t.children(TEST.a)), {TEST.b})
        self.assertEqual(set(t.children(TEST.b)), {TEST.c})
        self.assertEqual(set(t.children(TEST.c)), set())

    def test_transitive_decomposition_closure_last(self):
        """
        This test ensures that the tree that is constructed is "minimal" in the
        sense that the deductive closure of subclass relations is ignored.
        """
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.b, TEST.c)
        t.add(TEST.a, TEST.c)

        self.assertEqual(t.children(TEST.a), [TEST.b])
        self.assertEqual(t.children(TEST.b), [TEST.c])
        self.assertEqual(t.children(TEST.c), [])

    def test_transitive_decomposition_closure_first(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.c)
        t.add(TEST.a, TEST.b)
        t.add(TEST.b, TEST.c)

        self.assertEqual(t.children(TEST.a), [TEST.b])
        self.assertEqual(t.children(TEST.b), [TEST.c])
        self.assertEqual(t.children(TEST.c), [])

    def test_cycle_to_root(self):
        t = Taxonomy(TEST.a)
        self.assertRaises(error.Cycle, t.add, TEST.a, TEST.a)

    def test_1st_order_cycle(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        self.assertRaises(error.Cycle, t.add, TEST.b, TEST.b)

    def test_2nd_order_cycle(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.b, TEST.c)
        self.assertRaises(error.Cycle, t.add, TEST.c, TEST.b)

    def test_3rd_order_cycle(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.b, TEST.c)
        t.add(TEST.c, TEST.d)
        self.assertRaises(error.Cycle, t.add, TEST.d, TEST.b)

    def test_no_cycle(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.a, TEST.c)
        t.add(TEST.b, TEST.d)
        t.add(TEST.d, TEST.c)

    def test_non_unique_parent_relations(self):
        t = Taxonomy(TEST.a)
        t.add(TEST.a, TEST.b)
        t.add(TEST.a, TEST.c)
        t.add(TEST.b, TEST.d)
        self.assertRaises(error.NonUniqueParents, t.add, TEST.c, TEST.d)


if __name__ == '__main__':
    unittest.main()
