import unittest
from lovett.cs.transformer import TreeTransformer
from lovett.cs.searchfns import *
import lovett.tree as T

def leaf(label, word):
    return T.ParentedTree(label, [word])

PT = T.ParentedTree

class TestSearchFns(unittest.TestCase):
    def setUp(self):
        self.t = T.ParentedTree("""
                                ( (IP (ADVP (Q very) (ADV slowly)) (, ,)
                                (NP-SBJ (NPR John))
                                (V eats)
                                (NP-OB1 (D the) (ADJ tasty) (N apple))))""")
        self.tt = TreeTransformer(self.t)

    # TODO: test optional args, proper matching of dash labels, regex, etc.
    def test_hasLabel(self):
        self.tt.findNodes(hasLabel("N"))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

    def test_hasDaughter(self):
        self.tt.findNodes(hasDaughter(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [self.t[0]])

    def test_daughters(self):
        self.tt.findNodes(hasLabel("IP") & daughters(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [leaf("V", "eats")])

    def test_deep(self):
        self.tt.findNodes(hasLabel("IP") & deep(hasLabel("N")))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

    def test_iPrecedes(self):
        self.tt.findNodes(hasLabel("NPR") & iPrecedes(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [leaf("NPR", "John")])

    def test_not(self):
        self.tt.findNodes(hasLabel("IP") & daughters(~hasLabel("NP")))
        self.assertEqual(self.tt.matches(),
                         [PT("(ADVP (Q very) (ADV slowly))"),
                          PT("(, ,)"),
                          PT("(V eats)")])

    def test_hasAncestor(self):
        self.tt.findNodes(hasLabel("N") & hasAncestor(hasLabel("IP")))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

    def test_hasParent(self):
        self.tt.findNodes(hasLabel("N") & hasParent(hasLabel("NP")))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

    ##### Tests for ignoring()
    def test_ignoring_iPrecedes(self):
        self.tt.findNodes(hasLabel("ADV") &
                          ignoring(hasLabel(","),
                                   iPrecedes(hasLabel("NPR"))))
        self.assertEqual(self.tt.matches(), [leaf("ADV", "slowly")])

    def test_ignoring_daughters(self):
        self.tt.findNodes(hasLabel("NP") &
                          ignoring(hasLabel("ADJ"), daughters()))
        self.assertEqual(self.tt.matches(), [leaf("NPR", "John"),
                                             leaf("D", "the"),
                                             leaf("N", "apple")])


    # TODO: test hasLemma, other fns
