from lxml import etree

import collections.abc

class AnnotaldXmlError(Exception):
    pass

def _isMetaElement(x):
    return x.tag == "meta"

def _match(one, other):
    """Compare two ``lxml.etree._Element`` instances for equality.

    Checks, in turn, the tag, attributes, text (and tail), and children
    recursively.

    """
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

def _meta_to_deep(m, offset):
    if len(m) == 0:
        if m.tag == "meta":
            return ""
        return "%s(%s %s)" % (" " * offset, m.tag, m.text)
    else:
        l = m.tag
        if l == "meta":
            l = "META"
        c = list(map(lambda x: _meta_to_deep(x, offset + len(l) + 2), m))
        c[0] = c[0].lstrip()
        return " " * offset + ("(%s " % l) + "\n".join(c) + ")"

def _calc_trace(node):
    m = node.metadata()
    i = m.get("index", None)
    it = m.get("idxtype", None)
    if i is not None and it is not None:
        del m["index"]
        del m["idxtype"]
        return ("=" if it == "gap" else "-") + i
    return ""


class TreeNode(etree.ElementBase):
    """Base class for all classes which represent elements in a PSDX tree.

    This class inherits from the `LXML ElementBase class
    <http://lxml.de/api/lxml.etree.ElementBase-class.html>`_.

    It implements equality based on comparing the XML tag, attributes, text,
    and children.  It throws an error on being accessed as an iterator, since
    this will return the metadata node mixed with bona fide children.  In
    order to iterate over children, use :func:`NonTerminal.children`.

    """
    def label(self):
        """Return the label for the node, composed from the ``category`` and
        ``subcategory`` attributes.

        :returns: The label of the node
        :rtype: str

        """

        cat = self.get("category")
        subcat = self.get("subcategory", None)
        if subcat is not None:
            return cat + "-" + subcat
        else:
            return cat

    def set_label(self, new_label):
        """Set the label of a node.

        The passed ``new_label`` can have at most two pieces separated by a
        dash.  The first will be assigned to the ``category`` attribute, and
        the second, if it exists, to the ``subcategory``.

        :param str new_label: the new label to set

        """

        p = new_label.split("-")
        self.attrib["category"] = p[0]
        if len(p) == 2:
            self.attrib["subcategory"] = p[1]
        elif len(p) > 2:
            raise AnnotaldXmlError("cannot set multiple dash tags in XML: " +
                                   new_label)

    def sentence_node(self):
        """Return the ``sentence`` node dominating a node.

        :rtype: :class:`Sentence`

        """

        p = self
        while True:
            p = p.getparent()
            if p is None:
                raise AnntoaldXmlError("could not find sentence for %r" % self)
            if p.tag == "sentence":
                return t

    def left_sibling(self):
        """Return the next sibling to the left of a node.

        :rtype: :class:`TreeNode`

        """

        return self.getprevious()

    def right_sibling(self):
        """Return the next sibling to the right of a node.

        :rtype: :class:`TreeNode`

        """
        return self.getnext()

    def metadata(self):
        """Return a dict-like object backed by a node's metadata.

        :rtype: :class:`MetadataDict`

        """

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
        return _match(self, other)

    def to_deep(self, offset):
        raise NotImplementedError()

    # Not pictured: parent_index, __hash__

class MetadataDict(collections.abc.MutableMapping):
    """A dict-like object backed by PSDX metadata.

    This class provides a dict-like intreface to python code which is backed
    by the ``<meta>`` tag of a PSDX node.  You should be careful about hanging
    on to references to these objects, since doing so may adversely affect
    memory usage by preventing lxml's Python proxy objects from being garbage
    collected.  (This supposition is not tested, though.)

    This class forbids accessing the following metadata keys, which should
    instead be assigned to attributes:  (TODO: link to PSDX doc)

    - ``category``
    - ``comtype``
    - ``ectype``
    - ``id``
    - ``subcategory``
    - ``tracetype``

    """

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
        r = self.element.find(item.lower())
        if r is not None:
            r.getparent().remove(r)

    def __len__(self):
        return len(self.element)

    def __iter__(self):
        yield from (x.tag for x in self.element)

class NonTerminal(TreeNode):
    """A class representing nonterminal PSDX nodes."""
    # not pictured: children, leaves, height, subtrees, pos, map_leaves,
    # filter_leaves, to_xml, __str__
    def subtrees(self):
        """Access the subtrees of a nonterminal.

        Returns all subtrees in a node, including terminals, in `preorder
        <https://en.wikipedia.org/wiki/Tree_traversal#Pre-order>`_.

        :rtype: iterator

        """
        for t in self.children():
            if isinstance(t, Terminal):
                yield t
            else:
                yield t
                yield from t.subtrees()

    def children(self):
        """Access the children of a nonterminal.

        :rtype: Iterator

        """

        yield from (x for x in self.iterchildren() if not _isMetaElement(x))

    def to_deep(self, offset=0):
        l = self.label()
        c = list(map(lambda x: x.to_deep(offset + len(l) + 2), self.children()))
        c[0] = c[0].lstrip()
        m = self.find("meta")
        if m is not None:
            c.append(_meta_to_deep(m, offset + len(l) + 2))
        return " " * offset + ("(%s " % l) + "\n".join(c) + ")"

    def urtext(self):
        # TODO: join split words
        return " ".join(filter(lambda x: x != "",
                               (s.urtext() for s in self if s.tag != "meta")))


class Sentence(etree.ElementBase):
    """A class representing a sentence PSDX node."""
    def tree(self):
        """Get the tree that corresponds to the sentence.

        :rtype: :class:`TreeNode`

        """

        # TODO: falls over on metadata
        return self[0]

    def id(self):
        """Get the ID of a sentence.

        :rtype: str

        """

        return self.get("id", None)

    def set_id(self, new_id):
        """Set the ID of a sentence.

        :param str newid:

        """

        self.set("id", new_id)

    def to_deep(self):
        return "( " + self.tree().to_deep(2).lstrip() + ("\n  (ID %s))" % self.id())

class Terminal(TreeNode):
    """A class representing a terminal node."""
    def urtext(self):
        return ""

class Text(Terminal):
    """A class representing a text node."""
    def to_deep(self, offset=0):
        # Calculate whether the linearly preceding node has_continuation...
        def acceptable(x):
            return x is not None and x is not self and x.tag in ["text", "trace", "ec"]
        pre_dollar = False
        p = self
        while not acceptable(p):
            if p is None:
                break
            if p.tag == "nonterminal":
                # drop down a level
                p = p[len(p)-1]
                continue
            if p.getprevious() is None:
                if p.getparent() is None or p.getparent().tag == "sentence":
                    break
                p = p.getparent().getprevious()
            else:
                p = p.getprevious()
        if p is not None and p.metadata().get("has_continuation", None) == "yes":
            pre_dollar = True
        # ...back to our regularly scheduled programming
        m = self.find("meta")
        ms = ""
        l = self.label()
        ts = _calc_trace(self)
        if m is not None:
            ms = _meta_to_deep(m, offset + len(l) + 2)
            if ms != "":
                ms = "\n" + ms
        return "%s(%s%s (ORTHO %s%s%s)%s)" % \
            (" " * offset,
             l,
             ts,
             "$" if pre_dollar else "",
             self.text,
             "$" if self.metadata().get("has_continuation", None) == "yes" else "",
             ms)

    def urtext(self):
        return self.text

class Trace(Terminal):
    """A class representing a trace node."""
    # TODO: implement validation in _init method, e.g. must have index.  Else
    # assign unused index from the root tree.  Make it so reparenting an index
    # will reassign a unique value.

    def tracetype(self):
        """Get the type of a trace.

        :rtype: str

        """
        return self.get("tracetype", None)

    def set_tracetype(self, newtype):
        """Set the type of a trace.

        :param str newtype:

        """
        self.set("tracetype", newtype)

    def to_deep(self, offset=0):
        m = self.find("meta")
        ms = ""
        l = self.label()
        ts = _calc_trace(self)
        if m is not None:
            ms = _meta_to_deep(m, offset + len(l) + 2)
            if ms != "":
                ms = "\n" + ms
        else:
            raise AnnotaldXmlError("traces must have metadata")
        return "%s(%s (ALT-ORTHO %s%s)%s)" % (" " * offset,
                                              l,
                                              "*" + self.tracetype() + "*",
                                              ts,
                                              ms)

class Ec(Terminal):
    """A class representing an empty category node."""

    def ectype(self):
        """Get the type of an empty category.

        :rtype: str

        """
        return self.get("ectype", None)

    # TODO: validate data
    def set_ectype(self, newtype):
        """Set the type of an empty category.

        :param str newtype:

        """
        self.set("ectype", newtype)

    def to_deep(self, offset=0):
        m = self.find("meta")
        ms = ""
        l = self.label()
        ts = _calc_trace(self)
        if m is not None:
            ms = _meta_to_deep(m, offset + len(l) + 2)
            if ms != "":
                ms = "\n" + ms
        if self.ectype() == "zero":
            ect = "0"
        elif self.ectype() == "star":
            ect = "*"
        else:
            ect = "*" + self.ectype() + "*"
        return "%s(%s%s (ALT-ORTHO %s)%s)" % (" " * offset, l, ts, ect, ms)

class Comment(Terminal):
    """A class representing a comment node."""

    def label(self):
        """Get the label of a comment node.

        Always returns ``"CODE"``.

        """
        return "CODE"

    def set_label(self, newlabel):
        """Set the label of a comment node.

        Always raises an exception.

        """
        raise AnnotaldXmlError("cannot set the label of a comment node")

    def comtype(self):
        """Get the type of a comment.

        :rtype: str

        """
        return self.get("comtype", None)

    def set_comtype(self, newtype):
        """Set the type of a comment.

        :param str newtype:

        """
        self.set("comtype", newtype)

    def to_deep(self, offset=0):
        return " " * offset + "(CODE (ALT-ORTHO {%s:%s}))" % \
            (self.comtype(), self.text.replace(" ", "_"))

    def metadata(self):
        raise AnnotaldXmlError("Comments don't have metadata")
