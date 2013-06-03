from __future__ import unicode_literals

import unittest
import textwrap

import lovett.tree_new as TN
from lovett.tree_new import NonTerminal as NT
from lovett.tree_new import Leaf as L

class UtilFnsTest(unittest.TestCase):

    def test_parse(self):
        self.assertIsNone(TN.parse(""))
        self.assertIsNone(TN.parse("  \n  "))
        self.assertRaises(TN.ParseError, lambda: TN.parse("(FOO"))
        self.assertRaises(TN.ParseError, lambda: TN.parse("(FOO))"))
        self.assertRaises(TN.ParseError, lambda: TN.parse("(FOO)"))
        self.assertRaises(TN.ParseError, lambda: TN.parse("(FOO bar baz)"))


class TreeTest(unittest.TestCase):
    def test_label(self):
        t = L("foo", "bar")
        self.assertEqual(t.label, "foo")
        t.label = "baz"
        self.assertEqual(t.label, "baz")
        def foo(x):
            x.label = ''
        self.assertRaises(ValueError, foo, t)

    def test_parent_index(self):
        t = NT("foo", [L("bar", "BAR"), L("baz", "BAZ")])
        for i, v in enumerate(t):
            self.assertEqual(v.parent_index, i)
            self.assertEqual(t[v.parent_index], v)
        self.assertIsNone(t.parent_index)

    def test_siblings(self):
        l1 = L("bar", "BAR")
        l2 = L("baz", "BAZ")
        t = NT("foo", [l1,l2])
        self.assertIs(l1.right_sibling, l2)
        self.assertIs(l2.left_sibling, l1)
        self.assertIsNone(l1.left_sibling)
        self.assertIsNone(l2.right_sibling)

    def test_root(self):
        l = L("a", "b")
        t = NT("foo",[NT("bar", [l])])
        self.assertIs(l.root, t)

    def test_str_indices(self):
        t = TN.parse("( (IP=1 (FOO bar)))")
        self.assertEqual(str(t), "( (IP=1 (FOO bar)))")

class RootTest(unittest.TestCase):
    def test_parse_1(self):
        t = TN.parse("( (METADATA (X 1)) (ID foo) (IP (NP (PRO it)) (VBP works)))")
        self.assertIsInstance(t, TN.Root)
        self.assertEqual(t.metadata, {'X' : '1'})
        self.assertEqual(t.id, 'foo')
        self.assertEqual(t[0], NT("IP", [NT("NP", [L("PRO", "it")]), L("VBP", "works")]))

    def test_str(self):
        t = TN.parse("""( (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming))))""")
        s = str(t)
        self.assertIsInstance(s, str)
        self.assertMultiLineEqual(s, textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming))))
            """).strip())

    def test_id(self):
        t = TN.parse("""( (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming)))(ID foo))""")
        # Test that ID is parsed
        self.assertEqual(t.id, "foo")
        # Test that str works
        s = str(t)
        self.assertIsInstance(s, str)
        self.assertMultiLineEqual(s, textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming)))
              (ID foo))
            """).strip())
        t2 = TN.parse("""( (ID foo)(IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming))))""")
        # Test that the order of the ID node doesn't matter to parsing
        self.assertEqual(t2.id, "foo")
        self.assertEqual(t, t2)
        self.assertEqual(hash(t), hash(t2))
        self.assertEqual(s, str(t2))

    def test_metadata(self):
        t = TN.parse("""( (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming)))(METADATA (AOO bar)
        (BOO (A 1) (B 2))))""")
        # Test that ID is parsed
        self.assertEqual(t.metadata, { 'AOO': 'bar',
                                       'BOO': { 'A': '1',
                                                'B': '2' } })
        # Test that str works
        s = str(t)
        self.assertIsInstance(s, str)
        self.assertMultiLineEqual(s, textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming)))
              (METADATA (AOO bar)
                        (BOO (A 1)
                             (B 2))))
            """).strip())
        t2 = TN.parse("""( (METADATA (BOO (A 1) (B 2)) (AOO bar)
        ) (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming))))""")
        # Test that the order of the METADATA node doesn't matter to parsing
        self.assertEqual(t2.metadata, { 'AOO': 'bar',
                                        'BOO': { 'A': '1',
                                                 'B': '2' } })
        self.assertEqual(t, t2)
        self.assertEqual(hash(t), hash(t2))
        self.assertEqual(s, str(t2))

    def test_bad_metadata(self):
        md = "( (FOO (BAR baz)) (ID foobar-1) (METADATA (AUTHOR me)) (BAD metadata))"
        self.assertRaises(TN.ParseError, TN.parse, md)

    def test_metadata_id(self):
        t = TN.parse("""( (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming)))(METADATA (AOO bar)
        (BOO (A 1) (B 2))) (ID foo))""")
        self.assertMultiLineEqual(str(t), textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming)))
              (METADATA (AOO bar)
                        (BOO (A 1)
                             (B 2)))
              (ID foo))
            """).strip())

    def test_parent(self):
        r = TN.Root(None, L("foo", "bar"))
        self.assertIsNone(r.parent)
        t = NT("a", [L("b", "c")])
        self.assertRaises(ValueError, lambda: t.append(r))

    def test_mutating(self):
        r = TN.Root(None, L("foo", "bar"))
        def foo(x):
            del x[0]
        def bar(x):
            x[1] = L("foo", "bar")
        def baz(x):
            x.insert(1, L("foo", "bar"))
        self.assertRaises(ValueError, foo, r)
        self.assertRaises(ValueError, baz, r)
        self.assertRaises(ValueError, bar, r)
        r[0] = L("baz", "quux")
        self.assertEqual(r, TN.Root(None, L("baz", "quux")))


class LeafTest(unittest.TestCase):
    class MockCorpus(object):
        def __init__(self, version):
            self.version = version

    def assertStrs(self, leaf, strs):
        leaf.corpus = self.MockCorpus("old-style")
        self.assertEqual(str(leaf), strs[0])
        leaf.corpus = self.MockCorpus("dash")
        self.assertEqual(str(leaf), strs[1])
        leaf.corpus = self.MockCorpus("deep")
        self.assertEqual(str(leaf), strs[2])

    def test_str(self):
        l = L("FOO", "bar")

        self.assertStrs(l,
                        ["(FOO bar)",
                         "(FOO bar)",
                         "(FOO (ORTHO bar))"])
        l = L("FOO-1", "bar")
        self.assertStrs(l,
                        ["(FOO-1 bar)",
                         "(FOO-1 bar)",
                         textwrap.dedent(
                        """
                        (FOO (ORTHO bar)
                             (METADATA (IDX-TYPE regular)
                                       (INDEX 1)))""").strip()])
        l = L("FOO", "bar")
        l.metadata['LEMMA'] = "baz"
        self.assertStrs(l,
                        ["(FOO bar)",
                         "(FOO bar-baz)",
                         textwrap.dedent(
                             """
                             (FOO (ORTHO bar)
                                  (METADATA (LEMMA baz)))""").strip()])

        l = L("FOO", "*T*-1")
        self.assertStrs(l,
                        ["(FOO *T*-1)",
                         "(FOO *T*-1)",
                         textwrap.dedent(
                         """
                         (FOO (METADATA (ALT-ORTHO *T*)
                                        (IDX-TYPE regular)
                                        (INDEX 1)))""").strip()])
    def test_mult_daughters(self):
        anomalous = "(FOO (BAR baz quux))"
        self.assertRaises(TN.ParseError, TN.parse, anomalous)
