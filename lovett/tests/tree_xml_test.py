import testtools
import lxml.etree

from lovett.corpus import parse_string

class TreeXmlTest(testtools.TestCase):
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
