import unittest
from lovett.cs.transformer import TreeTransformer
from lovett.cs.searchfns import *
import lovett.cs.searchfns
import lovett.tree as T

def leaf(label, word):
    return T.LovettTree(label, [word])

LT = T.LovettTree.parse

class TestSearchFns(unittest.TestCase):
    def setUp(self):
        self.t = LT("""
        ( (IP (ADVP (Q very) (ADV slowly)) (, ,)
        (NP-SBJ (NPR John))
        (V eats)
        (NP-OB1 (D the) (ADJ tasty) (N apple))))""")
        self.tt = TreeTransformer(self.t)

    # TODO: test optional args, proper matching of dash labels, regex, etc.
    def test_hasLabel(self):
        self.tt.findNodes(hasLabel("N"))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

        self.tt.findNodes(hasLabel("NP"))
        self.assertEqual(self.tt.matches(),
                         [LT("(NP-SBJ (NPR John))"),
                          LT("(NP-OB1 (D the) (ADJ tasty) (N apple))")])

        self.tt.findNodes(hasLabel("NP", exact=True))
        self.assertEqual(self.tt.matches(), [])

    def test_hasDaughter(self):
        self.tt.findNodes(hasDaughter(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [self.t[0]])

    def test_daughters(self):
        self.tt.findNodes(hasLabel("IP") & daughters(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [leaf("V", "eats")])

    def test_deep(self):
        self.tt.findNodes(hasLabel("IP") & deep(hasLabel("N")))
        l = list(self.tt.matches())
        print (repr(l))
        self.assertEqual(self.tt.matches(), [leaf("N", "apple")])

    def test_iPrecedes(self):
        self.tt.findNodes(hasLabel("NPR") & iPrecedes(hasLabel("V")))
        self.assertEqual(self.tt.matches(), [leaf("NPR", "John")])

    def test_not(self):
        self.tt.findNodes(hasLabel("IP") & daughters(~hasLabel("NP")))
        self.assertEqual(self.tt.matches(),
                         [LT("(ADVP (Q very) (ADV slowly))"),
                          LT("(, ,)"),
                          LT("(V eats)")])

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

    def test_str(self):
        def is_search_fn(x):
            if hasattr(x, "__call__"):
                try:
                    return isinstance(x("foo"), SearchFunction)
                except:
                    return False
        search_fns = set(map(lambda x: x.__name__, filter(is_search_fn, lovett.cs.searchfns.__dict__.values())))
        search_fns.remove("setIgnore")
        # TODO: test these
        search_fns.remove("sharesLabelWithMod")
        search_fns.remove("daughterCount")
        search_fns.remove("sharesLabelWith")
        # Remove unexported functions
        search_fns = search_fns.intersection(set(globals().keys()))

        self.assertGreater(len(search_fns), 0)

        for sf in search_fns:
            print (sf)
            s = "%s('foo')" % sf
            i = eval(s)
            self.assertEqual(s, str(i))

    @unittest.expectedFailure
    def test_startswith(self):
        self.tt.findNodes(hasWord(startsWith("t")))
        self.assertEqual(self.tt.matches(),
                         [leaf("D", "the"),
                          leaf("ADJ", "tasty")])
