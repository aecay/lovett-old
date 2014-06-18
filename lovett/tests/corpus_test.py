import testtools
from testtools.matchers import (Not, IsInstance)
from ..corpus import (parse_string, _validate_psdx, Corpus)
from .utils import PassesValidation
from ..tree import (Sentence, NonTerminal, Text, Trace, Ec, Comment)

def T(string):
    return _validate_psdx(parse_string(string))

class TestCorpusXml(testtools.TestCase):
    def test_validator(self):
        self.assertThat(T(
            """
            <corpus>
            <sentence id="XYZ">
            <text category="FOO">
            bar
            </text>
            </sentence>
            </corpus>
            """
        ), PassesValidation())

    def test_validator_fail(self):
        self.assertThat(T(
            """
            <corpus>
            <sentence d="XYZ">
            <text category="FOO">
            bar
            </text>
            </sentence>
            </corpus>
            """
        ), Not(PassesValidation()))

    def test_parser(self):
        cases = (("corpus", Corpus),
                 ("sentence", Sentence),
                 ("nonterminal", NonTerminal),
                 ("trace", Trace),
                 ("ec", Ec),
                 ("text", Text),
                 ("comment", Comment))
        for case in cases:
            parsed = parse_string("<%s/>" % case[0])
            self.expectThat(parsed, IsInstance(case[1]))
