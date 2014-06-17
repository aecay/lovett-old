import pkg_resources

from lxml import etree
from .tree import (Sentence, NonTerminal, Text, Trace, Ec, Comment)

# TODO: __all__ etc.

class Corpus(etree.ElementBase):
    def trees(self):
        # TODO: filter out meta crap
        return iter(self)

_lookup = etree.ElementNamespaceClassLookup()
_ns = _lookup.get_namespace(None)
# Annoyance: xml generated from a browser is typically case-insensitive,
# whereas in Python-land case matters.  We define both upper and lowercase
# versions, to be safe.
for p in (("corpus", Corpus),
          ("sentence", Sentence),
          ("nonterminal", NonTerminal),
          ("trace", Trace),
          ("ec", Ec),
          ("text", Text),
          ("comment", Comment)):
    _ns[p[0]] = p[1]
    _ns[p[0].upper()] = p[1]
parser = etree.XMLParser(remove_blank_text=True)
parser.set_element_class_lookup(_lookup)

def parse_string(s):
    r = etree.fromstring(s, parser=parser)
    return _postprocess_parsed(r)

def parse_file(file):
    r = etree.parse(file, parser=parser)
    return _postprocess_parsed(r)

def _postprocess_parsed(r):
    for x in r.iter():
        x.tag = x.tag.lower()
    return r

_psdx_rng = None
def _validate_psdx(corpus):
    global _psdx_rng
    if _psdx_rng is None:
        _psdx_rng = etree.RelaxNG(etree.parse(pkg_resources.resource_stream(
            "lovett", "data/psdx.rng"
        )))
    if _psdx_rng.validate(corpus):
        return True, None
    else:
        return False, _psdx_rng.error_log.last_error
