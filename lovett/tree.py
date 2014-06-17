from lxml import etree

import collections.abc

class AnnotaldXmlError(Exception):
    pass

def isMetaElement(x):
    return x.tag == "meta"

def _match(one, other):
    if one.tag != other.tag:
        return False
    for name, value in one.attrib.items():
        if other.attrib.get(name) != value:
            return False
    for name in other.attrib.keys():
        if name not in one.attrib.keys():
            return False
    if not one.text == other.text:
        return False
    if not one.tail == other.tail:
        return False
    cl1 = one.getchildren()
    cl2 = other.getchildren()
    if len(cl1) != len(cl2):
        return False
    for c1, c2 in zip(cl1, cl2):
        m = _match(c1, c2)
        if not m:
            return False
    return True

class TreeNode(etree.ElementBase):
    def label(self):
        cat = self.get("category")
        subcat = self.get("subcategory", None)
        if subcat is not None:
            return cat + "-" + subcat
        else:
            return cat

    def set_label(self, newLabel):
        p = newLabel.split("-")
        self.attrib["category"] = p[0]
        if len(p) == 2:
            self.attrib["subcategory"] = p[1]
        if len(p) > 2:
            raise AnnotaldXmlError("cannot set multiple dash tags in XML: " +
                                   newLabel)

    def urtext(self):
        # TODO:
        # - join continued words
        # - remove spaces before punctuation
        # look at using etree.XPath("//text()") to get a list of in-order text
        # chunks...
        # or: traverse the tree in order, push text (and appropriate spaces)
        # onto a list, concat and return
        return etree.tostring(self, method="text")

    def sentence_node(self):
        p = self
        while True:
            p = p.getparent()
            if p is None:
                raise AnntoaldXmlError("could not find sentence for %r" % self)
            if p.tag == "sentence":
                return t

    def left_sibling(self):
        return self.getprevious()

    def right_sibling(self):
        return self.getnext()

    def metadata(self):
        meta = self.find("meta")
        if meta is None:
            meta = self.makeelement("meta")
            self.insert(0, meta)
        return MetadataDict(meta)

    def _strip_empty_meta(self):
        for m in self.getiterator("meta"):
            if len(m) == 0:
                t = m.tail
                p = m.getparent()
                p.remove(m)
                if t is not None and t != "":
                    p.text = p.text or ""
                    p.text += t

    def __iter__(self):
        raise AnnotaldXmlError("you shouldn't iterate directly over an element, you'll bogusly find metadata")

    def __eq__(self, other):
        if not isinstance(other, etree._Element):
            return False
        self._strip_empty_meta()
        try:
            other._strip_empty_meta()
        except AttributeError:
            pass
        print(etree.tostring(self))
        print(etree.tostring(other))
        return _match(self, other)

    # Not pictured: parent_index, __eq__, __hash__

class MetadataDict(collections.abc.MutableMapping):
    # TODO: make a forbidden metadata items property on the class; if we try
    # to set a forbidden metadata item throw an error.  Forbidden metadata
    # will be things like category, tracetype (for traces) etc. which should
    # be set as attrs and not metadata
    def __init__(self, element):
        self.element = element

    def __getitem__(self, item):
        r = self.element.find(item.lower())
        if r is None:
            raise KeyError
        if len(r) > 0:
            return MetadataDict(r)
        return r.text

    def __setitem__(self, item, val):
        if item in ["tracetype", "ectype", "category", "subcategory",
                    "comtype", "id"]:
            raise AnnotaldXmlError(
                "Key '%s' should be set as an attribute, not metadata" % item)
        r = self.element.find(item.lower())
        if r is None:
            r = self.element.makeelement(item.lower())
            self.element.append(r)
        if hasattr(val, "items"):
            smd = MetadataDict(r)
            for k, v in val.items():
                smd[k] = v
        else:
            r.text = val

    def __delitem__(self, item):
        raise NotImplementedError()

    def __len__(self):
        return len(self.element)

    def __iter__(self):
        yield from (x.tag for x in self.element)

class NonTerminal(TreeNode):
    # not pictured: children, leaves, height, subtrees, pos, map_leaves,
    # filter_leaves, to_xml, __str__
    def subtrees(self):
        for t in self.children():
            if isinstance(t, Terminal):
                yield t
            else:
                yield t
                yield from t.subtrees()

    def children(self):
        yield from (x for x in self.iterchildren() if not isMetaElement(x))

class Sentence(etree.ElementBase):
    def tree(self):
        # TODO: falls over on metadata
        return self[0]

    def id(self):
        return self.get("id", None)

    def set_id(self, newid):
        self.set("id", new_id)

class Terminal(TreeNode):
    pass

class Text(Terminal):
    pass

class Trace(Terminal):
    # TODO: implement validation in _init method, e.g. must have index.  Else
    # assign unused index from the root tree.  Make it so reparenting an index
    # will reassign a unique value.

    # TODO: need another tracetype: zero, amovt, and etc.
    pass

class Ec(Terminal):
    pass

class Comment(Terminal):
    # TODO: use XML comments??
    pass
