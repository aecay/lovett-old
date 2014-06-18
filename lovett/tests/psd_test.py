import testtools
import lovett.psd_tree
import lovett.psd
from lxml.etree import tostring as S
from .utils import MatchesXml

PsdTree = lovett.psd_tree.Tree

def P(s):
    return lovett.psd._parse_terminal(PsdTree.parse(s))

class TestPsd(testtools.TestCase):
    def test_parse_terminal(self):
        self.assertThat(P("(FOO *T*-1)"),
                        MatchesXml("""
                        <trace category=\"FOO\" tracetype=\"T\">
                        <meta>
                        <index>1</index>
                        <idxtype>regular</idxtype>
                        </meta>
                        </trace>
                        """))
