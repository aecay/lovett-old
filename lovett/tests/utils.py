from testtools.matchers import Mismatch
import lxml.etree

def _match(one, other):
    if one.tag != other.tag:
        return Mismatch("Tag mismatch:\n%s\n\n%s" %
                        (lxml.etree.tostring(other),
                         lxml.etree.tostring(one)))
    for name, value in one.attrib.items():
        if other.attrib.get(name) != value:
            return Mismatch("Attrib mismatch %s:\n%s\n\n%s" %
                            (name,
                             lxml.etree.tostring(other),
                             lxml.etree.tostring(one)))
    for name in other.attrib.keys():
        if name not in one.attrib.keys():
            return Mismatch("Extra attrib %s:\n%s\n\n%s" %
                            (name,
                             lxml.etree.tostring(other),
                             lxml.etree.tostring(one)))
    if not one.text == other.text:
        return Mismatch("Text mismatch:\n%s\n\n%s" %
                        (lxml.etree.tostring(other),
                         lxml.etree.tostring(one)))
    if not one.tail == other.tail:
        return Mismatch("Tail mismatch:\n%s\n\n%s" %
                        (lxml.etree.tostring(other),
                         lxml.etree.tostring(one)))
    cl1 = one.getchildren()
    cl2 = other.getchildren()
    if len(cl1) != len(cl2):
        return Mismatch("Length mismatch:\n%s\n\n%s" %
                        (lxml.etree.tostring(other),
                         lxml.etree.tostring(one)))
    for c1, c2 in zip(cl1, cl2):
        m = _match(c1, c2)
        if m is not None:
            return m
    return None

class MatchesXml(object):
    def __init__(self, xml):
        parser = lxml.etree.XMLParser(remove_blank_text=True)
        self.xml = lxml.etree.fromstring(xml, parser=parser)

    def __str__(self):
        return "MatchesXml(\"%s\")" % lxml.etree.tostring(self.xml)

    def match(self, other):
        return _match(self.xml, other)

class PassesValidation(object):
    def __init__(self):
        pass

    def match(self, res):
        if res[0]:
            return None
        else:
            return Mismatch(str(res[1]))
