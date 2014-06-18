import testtools
import lxml.etree

from lovett.corpus import parse_string

class TreeTest(testtools.TestCase):
    def test_eq(self):
        one = parse_string("<text category=\",\">,</text>")
        two = parse_string("<text category=\",\">,</text>")
        self.assertEqual(one, two)

    def test_neq(self):
        one = parse_string("<text category=\",\">,</text>")
        two = parse_string("<text category=\",\">.</text>")
        self.assertNotEqual(one, two)

    def test_eq_plain_rhs(self):
        one = parse_string("<text category=\",\">,</text>")
        two = lxml.etree.fromstring("<text category=\",\">,</text>")
        self.assertEqual(one, two)

    def test_eq_plain_lhs(self):
        two = parse_string("<text category=\",\">,</text>")
        one = lxml.etree.fromstring("<text category=\",\">,</text>")
        self.assertEqual(one, two)

    def test_eq_empty_meta(self):
        one = parse_string("<text category=\",\"><meta/>,</text>")
        two = parse_string("<text category=\",\">,</text>")
        self.assertEqual(one, two)

    # TreeNode
    def test_label(self):
        self.skipTest("unwritten test")

    def test_set_label(self):
        self.skipTest("unwritten test")

    def test_urtext(self):
        self.skipTest("unwritten test")

    def test_sentence_node(self):
        self.skipTest("unwritten test")

    def test_left_sibling(self):
        self.skipTest("unwritten test")

    def test_right_sibling(self):
        self.skipTest("unwritten test")

    def test_iter(self):
        self.skipTest("unwritten test")

    # MetadataDict

    def test_illegal_attrs(self):
        self.skipTest("unwritten test")

    # NonTerminal

    def test_children(self):
        self.skipTest("unwritten test")

    def test_subtrees(self):
        self.skipTest("unwritten test")

    # Sentence
    def test_tree(self):
        self.skipTest("unwritten test")

    def test_id(self):
        self.skipTest("unwritten test")

    def test_set_id(self):
        self.skipTest("unwritten test")
