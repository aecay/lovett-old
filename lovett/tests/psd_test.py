import testtools
import lovett.psd_tree
import lovett.psd as Psd
import lxml.etree
from .utils import MatchesXml
from lovett.corpus import parse_string as xml_parse_string
from lovett.corpus import parse_file as xml_parse_file

PsdTree = lovett.psd_tree.Tree.parse

import pkg_resources

class TestPsd(testtools.TestCase):
    def test_parse_trace(self):
        self.assertThat(Psd._parse_terminal(PsdTree("(FOO *T*-1)")),
                        MatchesXml("""
                        <trace category=\"FOO\" tracetype=\"T\">
                        <meta>
                        <index>1</index>
                        <idxtype>regular</idxtype>
                        </meta>
                        </trace>
                        """))

    def test_parse_trace(self):
        self.assertThat(Psd._parse_terminal(PsdTree("(FOO *T*-1)")),
                        MatchesXml("""
                        <trace category=\"FOO\" tracetype=\"T\">
                        <meta>
                        <index>1</index>
                        <idxtype>regular</idxtype>
                        </meta>
                        </trace>
                        """))

    def test_parse_psdx_string(self):
        s = lxml.etree.tostring(xml_parse_file(pkg_resources.resource_stream(
            "lovett", "tests/data/icepahc-test.psdx")))
        self.assertThat(Psd.parse_deep_string(xml_parse_string(s).to_deep()),
                        MatchesXml(s))
