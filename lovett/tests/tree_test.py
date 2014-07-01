import testtools
import lxml.etree

from lovett.corpus import parse_string
from .utils import MatchesXml
from lovett.tree import AnnotaldXmlError
import lovett.tree

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

    def test_meta_to_deep(self):
        m = lxml.etree.fromstring("<meta><x>y</x></meta>")
        self.assertEqual(lovett.tree._meta_to_deep(m, 0),
                         "(META (x y))")

class TreeNodeTest(testtools.TestCase):
    # TreeNode
    def test_label(self):
        s = parse_string("<text category=\"FOO\">bar</text>")
        self.assertEqual(s.label(), "FOO")

    def test_label_subcat(self):
        s = parse_string("<text category=\"FOO\" subcategory=\"BAR\">baz</text>")
        self.assertEqual(s.label(), "FOO-BAR")

    def test_set_label(self):
        s = parse_string("<text category=\"FOO\">bar</text>")
        s.set_label("BAR")
        self.assertThat(s, MatchesXml(
            "<text category=\"BAR\">bar</text>"
        ))

    def test_set_label_subcat(self):
        s = parse_string("<text category=\"FOO\">bar</text>")
        s.set_label("BAR-QUUX")
        self.assertThat(s, MatchesXml(
            "<text category=\"BAR\" subcategory=\"QUUX\">bar</text>"
        ))

    def test_set_label_raises(self):
        s = parse_string("<text category=\"FOO\">bar</text>")
        self.assertRaises(AnnotaldXmlError,
                          lambda: s.set_label("FOO-BAR-BAZ"))

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

class MetadataDictTest(testtools.TestCase):
    def test_illegal_attrs(self):
        self.skipTest("unwritten test")

class NonTerminalTest(testtools.TestCase):
    def test_children(self):
        self.skipTest("unwritten test")

    def test_subtrees(self):
        self.skipTest("unwritten test")

    def test_to_deep(self):
        s = parse_string(
            """<nonterminal category=\"XYZ\">
            <text category=\"FOO\">BAR</text>
            <text category=\"FOO\" subcategory=\"BAZ\">BAR</text>
            <text category=\"FOO\">BAR<meta><x>y</x></meta></text>
            <trace category=\"FOO\" tracetype=\"T\"><meta><index>1</index><idxtype>regular</idxtype></meta></trace>
            <ec category=\"FOO\" ectype=\"pro\" />
            <comment comtype=\"FOO\">bar</comment>
            </nonterminal>"""
        )
        self.assertEqual(s.to_deep(),
                         """
(XYZ (FOO (ORTHO BAR))
     (FOO-BAZ (ORTHO BAR))
     (FOO (ORTHO BAR)
          (META (x y)))
     (FOO (ALT-ORTHO *T*-1))
     (FOO (ALT-ORTHO *pro*))
     (CODE (ALT-ORTHO {FOO:bar})))
                         """.strip())

    def test_to_deep_nested(self):
        s = parse_string(
            """<nonterminal category=\"XYZ\">
            <nonterminal category=\"ABC\">
            <text category=\"FOO\">BAR</text>
            </nonterminal>
            </nonterminal>""")
        self.assertEqual(s.to_deep(),
                         """
(XYZ (ABC (FOO (ORTHO BAR))))
                         """.strip())

    def test_to_deep_nested_multi_leaf(self):
        s = parse_string(
            """<nonterminal category=\"XYZ\">
            <nonterminal category=\"ABC\">
            <text category=\"FOO\">BAR</text>
            <text category=\"BAR\">123</text>
            </nonterminal>
            </nonterminal>""")
        self.assertEqual(s.to_deep(),
                         """
(XYZ (ABC (FOO (ORTHO BAR))
          (BAR (ORTHO 123))))
                         """.strip())

    def test_to_deep_nested_multi_nt(self):
        s = parse_string(
            """<nonterminal category=\"XYZ\">
            <nonterminal category=\"ABC\">
            <text category=\"FOO\">BAR</text>
            </nonterminal>
            <nonterminal category=\"DEF\">
            <text category=\"BAR\">123</text>
            </nonterminal>
            </nonterminal>""")
        self.assertEqual(s.to_deep(),
                         """
(XYZ (ABC (FOO (ORTHO BAR)))
     (DEF (BAR (ORTHO 123))))
                         """.strip())

    def test_to_deep_nested_multi_both(self):
        s = parse_string(
            """<nonterminal category=\"XYZ\">
            <nonterminal category=\"ABC\">
            <text category=\"FOO\">BAR</text>
            <text category=\"BAR\">123</text>
            </nonterminal>
            <nonterminal category=\"DEF\">
            <text category=\"FOO\">BAR</text>
            <text category=\"BAR\">123</text>
            </nonterminal>
            </nonterminal>""")
        self.assertEqual(s.to_deep(),
                         """
(XYZ (ABC (FOO (ORTHO BAR))
          (BAR (ORTHO 123)))
     (DEF (FOO (ORTHO BAR))
          (BAR (ORTHO 123))))
                         """.strip())

class SentenceTest(testtools.TestCase):
    def test_tree(self):
        self.skipTest("unwritten test")

    def test_id(self):
        self.skipTest("unwritten test")

    def test_set_id(self):
        self.skipTest("unwritten test")

    def test_to_deep(self):
        s = parse_string("<sentence id=\"XYZ\"><text category=\"FOO\">BAR</text></sentence>")
        self.assertEqual(s.to_deep(),
                         "( (FOO (ORTHO BAR))\n  (ID XYZ))")

    def test_to_deep_multi(self):
        s = parse_string("""<sentence id="XYZ">
        <nonterminal category="ABC">
        <text category="FOO">BAR</text>
        <text category="XYZ">123</text>
        </nonterminal>
        </sentence>""")
        self.assertEqual(s.to_deep(),
                         """
( (ABC (FOO (ORTHO BAR))
       (XYZ (ORTHO 123)))
  (ID XYZ))
                         """.strip())

class TerminalTest(testtools.TestCase):
    def test_to_deep(self):
        s = parse_string("<text category=\"FOO\">BAR</text>")
        self.assertEqual(s.to_deep(),
                         "(FOO (ORTHO BAR))")
    def test_to_deep_subcat(self):
        s = parse_string("<text category=\"FOO\" subcategory=\"BAZ\">BAR</text>")
        self.assertEqual(s.to_deep(),
                         "(FOO-BAZ (ORTHO BAR))")
    def test_to_deep_meta(self):
        s = parse_string("<text category=\"FOO\">BAR<meta><x>y</x></meta></text>")
        self.assertEqual(s.to_deep(),
                         """
(FOO (ORTHO BAR)
     (META (x y)))
                         """.strip())

    def test_to_deep_index(self):
        s = parse_string("<text category=\"FOO\">BAR<meta><index>1</index><idxtype>regular</idxtype></meta></text>")
        self.assertEqual(s.to_deep(),
                         """
(FOO-1 (ORTHO BAR))
                         """.strip())

    def test_to_deep_index_gap(self):
        s = parse_string("<text category=\"FOO\">BAR<meta><index>1</index><idxtype>gap</idxtype></meta></text>")
        self.assertEqual(s.to_deep(),
                         """
(FOO=1 (ORTHO BAR))
                         """.strip())

    def test_urtext(self):
        s = parse_string("<text category=\"FOO\">BAR</text>")
        self.assertEqual(s.urtext(), "BAR")

    def test_urtext_meta(self):
        s = parse_string("<text category=\"FOO\">BAR<meta><x>y</x></meta></text>")
        self.assertEqual(s.urtext(), "BAR")

class TraceTest(testtools.TestCase):
    def test_to_deep(self):
        s = parse_string("<trace category=\"FOO\" tracetype=\"T\"><meta><index>1</index><idxtype>regular</idxtype></meta></trace>")
        self.assertEqual(s.to_deep(),
                         """
(FOO (ALT-ORTHO *T*-1))
                         """.strip())
    def test_to_deep_gap(self):
        s = parse_string("<trace category=\"FOO\" tracetype=\"T\"><meta><index>1</index><idxtype>gap</idxtype></meta></trace>")
        self.assertEqual(s.to_deep(),
                         """
(FOO (ALT-ORTHO *T*=1))
                         """.strip())

class EcTest(testtools.TestCase):
    def test_to_deep(self):
        s = parse_string("<ec category=\"FOO\" ectype=\"pro\" />")
        self.assertEqual(s.to_deep(),
                         """(FOO (ALT-ORTHO *pro*))""".strip())

    def test_to_deep_zero(self):
        s = parse_string("<ec category=\"FOO\" ectype=\"zero\" />")
        self.assertEqual(s.to_deep(),
                         """(FOO (ALT-ORTHO 0))""".strip())

    def test_to_deep_star(self):
        s = parse_string("<ec category=\"FOO\" ectype=\"star\" />")
        self.assertEqual(s.to_deep(),
                         """(FOO (ALT-ORTHO *))""".strip())

    def test_to_deep_index(self):
        s = parse_string("<ec category=\"FOO\" ectype=\"pro\"><meta><index>1</index><idxtype>regular</idxtype></meta></ec>")
        self.assertEqual(s.to_deep(),
                         """
(FOO-1 (ALT-ORTHO *pro*))
                         """.strip())

    def test_to_deep_index_gap(self):
        s = parse_string("<ec category=\"FOO\" ectype=\"pro\"><meta><index>1</index><idxtype>gap</idxtype></meta></ec>")
        self.assertEqual(s.to_deep(),
                         """
(FOO=1 (ALT-ORTHO *pro*))
                         """.strip())

class CommentTest(testtools.TestCase):
    def test_to_deep(self):
        s = parse_string("<comment comtype=\"FOO\">bar</comment>")
        self.assertEqual(s.to_deep(),
                         """(CODE (ALT-ORTHO {FOO:bar}))""")

    def test_to_deep_space(self):
        s = parse_string("<comment comtype=\"FOO\">bar quux</comment>")
        self.assertEqual(s.to_deep(),
                         """(CODE (ALT-ORTHO {FOO:bar_quux}))""")

    def test_no_metadata(self):
        s = parse_string("<comment comtype=\"FOO\">bar</comment>")
        self.assertRaises(AnnotaldXmlError,
                          lambda: s.metadata())
