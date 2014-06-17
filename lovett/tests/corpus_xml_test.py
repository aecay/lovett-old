import testtools
from ..corpus import (parse_string, _validate_psdx)
from .utils import PassesValidation

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
