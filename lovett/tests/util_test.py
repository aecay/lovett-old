import unittest
from io import StringIO
import textwrap

import lovett.tree_new
import lovett.util

class UtilTest(unittest.TestCase):
    def test_treeToDict(self):
        t = lovett.tree_new.parse(
            "(METADATA (FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertEqual(lovett.util._treeToDict(t),
                         {"FOO": "bar",
                          "BAZ": {"QUUX": "1",
                                  "BLORFLE": "2"}})

    def test_parseVersionTree(self):
        t = lovett.tree_new.parse("""
                                   ( (VERSION (FORMAT dash)
                                              (SOMETHING else)))
                                   """)
        self.assertEqual(lovett.util._parseVersionTree(t),
                         {"FORMAT": "dash",
                          "SOMETHING": "else"})
        t = lovett.tree_new.parse(
            "( (FOO (FOO bar) (BAZ (QUUX 1) (BLORFLE 2))))")
        self.assertIsNone(lovett.util._parseVersionTree(t))

    def test_label_and_index(self):
        li = lovett.util.label_and_index
        self.assertEqual(li("FOO-1"), ("FOO", "regular", 1))
        self.assertEqual(li("FOO=1"), ("FOO", "gap", 1))
        self.assertEqual(li("FOO-BAR-1"), ("FOO-BAR", "regular", 1))
        self.assertEqual(li("FOO-BAR=1"), ("FOO-BAR", "gap", 1))
        self.assertEqual(li("FOO-123"), ("FOO", 'regular', 123))
        self.assertEqual(li("FOO=BAR-1"), ("FOO=BAR", "regular", 1))
        self.assertEqual(li("NP-1"), ("NP", "regular", 1))
        self.assertEqual(li("NP-FOO-1"), ("NP-FOO", "regular", 1))
        self.assertEqual(li("NP=1"), ("NP", "gap", 1))
        self.assertIsNone(li("NP")[1])
        self.assertIsNone(li("NP")[2])
        self.assertRaises(ValueError, li, "NP=FOO=BAR")

    def test_index(self):
        cases = [("(NP-1 (D foo))", 1, "-", 'regular'),
                 ("(NP *T*-1)", 1, "-", 'regular'),
                 ("(XP *ICH*-3)", 3, "-", 'regular'),
                 ("(XP *-34)", 34, "-", 'regular'),
                 ("(XP *CL*-1)", 1, "-", 'regular'),
                 ("(XP=4 (X foo))", 4, "=", 'gap'),
                 ("(XP *FOO*-1)", None, None, None),
                 ("(NP (D foo))", None, None, None)]
        for (s, i, ts, t) in cases:
            self.assertEqual(lovett.util.index(lovett.tree_new.parse(s)), i)
            self.assertEqual(lovett.util.index_type_short(
                lovett.tree_new.parse(s)), ts)
            self.assertEqual(lovett.util.index_type(lovett.tree_new.parse(s)),
                             t)

    def test_remove_index(self):
        cases = [("(NP-1 (D foo))", "(NP (D foo))"),
                 ("(NP *T*-1)", "(NP *T*)"),
                 ("(XP *ICH*-3)", "(XP *ICH*)"),
                 ("(XP *-34)", "(XP *)"),
                 ("(XP *CL*-1)", "(XP *CL*)"),
                 ("(XP=4 (X foo))", "(XP (X foo))"),
                 ("(XP *FOO*-1)", "(XP *FOO*-1)"),
                 ("(NP (D foo))", "(NP (D foo))")]
        for (orig, new) in cases:
            ot = lovett.tree_new.parse(orig)
            lovett.util.remove_index(ot)
            self.assertEqual(ot, lovett.tree_new.parse(new))
