from __future__ import unicode_literals

# Python standard libraries
import collections.abc
import copy

# Third party libraries
from lxml.builder import E
from lxml import etree
import six

# Lovett libraries
import lovett.util

# TODO: strip, keep only parsing function generating XML representation

# TODO: add public decorator to control exports

class Tree(collections.abc.Hashable):
    __slots__ = ["_parent", "_metadata", "_label"]

    # TODO: use __getattr__ to pass to metadata dict?
    def __init__(self, label, metadata=None):
        self._parent = None
        # TODO: we might want to parse metadata
        self._metadata = metadata or {}
        label, idxtype, idx = lovett.util.label_and_index(label)
        self._label = label
        if idx is not None:
            self._metadata['INDEX'] = idx
            # TODO: what's the standard name
            self._metadata['IDX-TYPE'] = idxtype

    def __hash__(self):
        return hash(str(self._key_tuple()))

    def __eq__(self, other):
        return self._key_tuple() == other._key_tuple()

    def _key_tuple(self):
        raise NotImplementedError

    def label(self):
        return self._label

    def metadata(self):
        # TODO: freeze before returning?
        return self._metadata

    def parent(self):
        return self._parent

    def set_label(self, new):
        new = new.strip()
        if new == '':
            raise ValueError('Nodes cannot have an empty label.')
        self._label = new

    def parent_index(self):
        if self._parent is None:
            return None
        for i, child in enumerate(self._parent):
            if child is self:
                return i
        raise ValueError("Tree not contained in its parent")

    def left_sibling(self):
        parent_index = self.parent_index()
        if self._parent and parent_index > 0:
            return self._parent[parent_index - 1]
        return None

    def right_sibling(self):
        parent_index = self.parent_index()
        if self._parent and parent_index < len(self._parent) - 1:
            return self._parent[parent_index + 1]
        return None

    def root(self):
        root = self
        while root._parent is not None:
            root = root._parent
        return root

    def urtext(self):
        r = " ".join(filter(lambda s: s != "", [l.urtext() for l in self]))
        r = r.replace("@ @", "")
        # Hacktacularly delete spaces before punctuation
        r = r.replace(" LOVETT_DEL_SP", "")
        # Also zap space-delete markers at the beginning of the string
        r = r.replace("LOVETT_DEL_SP", "")
        return r.strip()

class Leaf(Tree):
    __slots__ = ["_text"]

    # TODO: implement dict interface passthrough to metadata?
    def __init__(self, label, text, metadata=None):
        super(Leaf, self).__init__(label, metadata)
        self._text = text
        # TODO: lemma

    def __str__(self, indent=0):
        # TODO: handle metadata, lemma
        try:
            # TODO: we want every child in the tree to be able to get its
            # corpus, not just the root...how to manage? make this a property
            # of Tree which returns self.root.corpus?
            v = self.root().corpus()._metadata['FORMAT']
            # TODO: replace with .get(). hurf durf.
        except:
            v = "old-style"

        if v == "old-style" or v == "dash":
            idxstr = ''
            try:
                if self._metadata['INDEX'] is not None:
                    if self._metadata['IDX-TYPE'] == "gap":
                        idxstr = '='
                    else:
                        idxstr = '-'
                    idxstr += str(self._metadata['INDEX'])
            except:
                pass
            text = self._text
            if v == "dash":
                # TODO: need to do this conversion coming in as well
                # TODO: the code node check below may not be working
                if not lovett.util.is_code_node(self):
                    text = text.replace("-", "<dash>")
                lemma = self._metadata.get('LEMMA', None)
                if lemma is not None:
                    text += '-' + lemma
            if lovett.util.is_trace(self):
                return ''.join(['(', self._label, ' ', text, idxstr, ')'])
            else:
                return ''.join(['(', self._label, idxstr, ' ', text, ')'])
        elif v == "deep":
            return str(NonTerminal(self._label, [Leaf("ORTHO", self._text)],
                                   self._metadata))
        else:
            raise ValueError("unknown corpus format: %s" % v)

    def __repr__(self):
        return "Leaf(%s, %s, metadata=%r)" % (self._label, self._text,
                                              self._metadata)

    def _key_tuple(self):
        return ("leaf", self._label, self._text, self._metadata)

    def urtext(self):
        # TODO: more excluded node types
        if lovett.util.is_ec(self) or self._label == "CODE" or \
           self._label.startswith("CODING"):
            return ""
        if self._label in [",", "."]:
            # Punctuation: no spaces
            # TODO: grossly hacktacular!
            return "LOVETT_DEL_SP" + self._text
        return self._text

    def pos(self):
        yield self

    def to_xml(self):
        d = {'label': self._label}
        d.update(self._metadata)
        for key, val in six.iteritems(d):
            d[key] = str(val)
        r = E.leaf(self._text, **d)
        return r

    def text(self):
        return self._text

# TODO: move to another file
class NTCoder(object):
    def __init__(self, tree, corpus):
        self.tree = tree
        self.corpus = corpus

    def __getattr__(self, attr):
        try:
            coder = self.corpus.coders[attr]
        except KeyError:
            raise KeyError("no coder named %s is defined" % attr)
        return coder.codeTree(self.tree)

class NonTerminal(Tree, collections.abc.MutableSequence):
    __slots__ = ["_children"]

    # TODO: implement dict interface passthrough to metadata? -- complicated,
    # since this is already a different type of sequence
    def __init__(self, label, children, metadata=None):
        # TODO: use *args magic to not need the list brax around children?
        super(NonTerminal, self).__init__(label, metadata)
        # coerce to a list; we don't want any generators to sneak in
        self._children = list(children)
        for child in self._children:  # pragma: no branch
            child._parent = self

    ### Abstract methods

    # For Container
    def __contains__(self, obj):
        return self._children.__contains__(obj)

    # For Iterable
    def __iter__(self):
        return self._children.__iter__()

    # For Sized
    def __len__(self):
        return len(self._children)

    # For Sequence
    def __getitem__(self, index):
        return self._children[index]

    # For MutableSequence
    def __setitem__(self, index, value):
        value._parent = self
        self._children[index] = value
        # TODO: what should be returned???
        return self._children[index]

    def __delitem__(self, index):
        # TODO: is there a better way to do this?
        if isinstance(index, int):
            self._children[index].parent = None
        else:
            # index is a slice
            for child in self._children[index]:  # pragma: no branch
                child.parent = None
        # TODO: should something be returned?
        del self._children[index]

    def insert(self, index, value):
        value._parent = self
        return self._children.insert(index, value)

    def _key_tuple(self):
        return ("nonterminal", self._label, self._children, self._metadata)

    ### Properties
    def children(self):
        return self.__iter__()

    def leaves(self):
        for child in self:  # pragma: no branch
            if isinstance(child, NonTerminal):
                yield from child.leaves
            else:
                yield child

    def height(self):
        max_child_height = 0
        for child in self:  # pragma: no branch
            if isinstance(child, NonTerminal):
                max_child_height = max(max_child_height, child.height())
            else:
                max_child_height = max(max_child_height, 1)
        return 1 + max_child_height

    def subtrees(self):
        yield self
        for child in self:  # pragma: no branch
            if hasattr(child, 'subtrees'):
                yield from child.subtrees()
            else:
                yield child

    def pos(self):
        yield from (x for x in self.subtrees() if isinstance(x, Leaf))

    def code(self):
        return NTCoder(self, self._corpus)

    ### Methods

    def map_leaves(self, fn, *args):
        self._children = [fn(x, *args) for x in self]

    def filter_leaves(self, fn, *args):
        self._children = [x for x in self if fn(x, *args)]

    # Copying -- use copy.copy and copy.deepcopy

    # TODO: use our utility fns
    def __repr__(self):
        childstr = ", ".join(repr(c) for c in self)
        return '%s(%s, [%s], metadata=%r)' % (type(self).__name__, self._label,
                                              childstr, self._metadata)

    def __str__(self, indent=0):
        try:
            # TODO: we want every child in the tree to be able to get its
            # corpus, not just the root...how to manage? make this a property
            # of Tree which returns self.root.corpus?
            v = self.root().corpus()._metadata['FORMAT']
        except:
            v = "old-style"
        s = "(%s" % self._label
        m = copy.deepcopy(self._metadata)
        if v in ['old-style', 'dash']:
            idx = lovett.util.index(self)
            if idx is not None:
                s += lovett.util.index_type_short(self) + str(idx)
            # TODO: very kludgey, maybe make metadata_str handle these
            # exculsions automatically
            try:
                del m['INDEX']
            except KeyError:
                pass
            try:
                del m['IDX-TYPE']
            except KeyError:
                pass
        s += " "
        l = len(s)
        leaves = ("\n" + " " * (indent + l)).join(
            map(lambda x: x.__str__(indent + l), self))
        metadata = ""
        if m != {}:
            metadata = "\n" + " " * (indent + l) + \
                       lovett.util.metadata_str(m,
                                                "METADATA",
                                                indent + l)
        return "".join([s, leaves, metadata, ")"])

    def to_xml(self):
        d = {'label': self._label}
        d.update(self._metadata)
        for key, val in six.iteritems(d):
            d[key] = str(val)
        r = E.node(*[child.to_xml() for child in self],
                   **d)
        return r

class Root(NonTerminal):
    __slots__ = ["_id"]

    def __init__(self, id, tree, metadata=None):
        super(Root, self).__init__('', [tree], metadata)
        self._id = id

    def _key_tuple(self):
        return ("root", self._id, self[0], self._metadata)

    def __str__(self, indent=0):
        s = super(Root, self).__str__(indent)
        if self._id is not None:
            s = s[0:len(s) - 1] + "\n  (ID " + self._id + "))"
        return s

    def __repr__(self):
        s = super(Root, self).__repr__()
        s = "Root(" + s[7:len(s)]  # get rid of the empty label
        return s

    def id(self):
        return self._id

    def set_id(self, new_id):
        self._id = new_id

    def parent(self):
        return None

    def set_parent(self, new):
        if new is not None:
            raise ValueError('Cannot insert a Root into another tree.')

    def tree(self):
        return self[0]

    def set_tree(self, val):
        self[0] = val

    def insert(self, x, index):
        raise ValueError("Cannot insert into a Root")

    def __delitem__(self, index):
        raise ValueError("Cannot delete from a Root")

    def __setitem__(self, index, value):
        if index != 0:
            raise ValueError("Cannot only set item at index 0 of a root "
                             "(given: %s)", index)
        super(Root, self).__setitem__(index, value)

    # @property
    # def urtext(self):
    #     return self.tree.urtext

    def to_xml(self):
        d = {}
        if self._id:
            d['ID'] = self._id
        d.update(self._metadata)
        for key, val in six.iteritems(d):
            d[key] = str(val)
        return E.sent(self[0].to_xml(), **d)

class ParseError(Exception):
    pass

def _tokenize(string):
    # TODO: corpussearch comments
    tok = ''
    for char in string:
        if char == '(' or char == ')':
            if tok != '':
                yield tok
                tok = ''
            yield char
        elif char in ' \n\t':
            if tok != '':
                yield tok
                tok = ''
            continue
        else:
            tok += char

def _list_to_dict(l):
    if isinstance(l[0], str):
        if isinstance(l[1], str):
            return l
        return (l[0], dict(list(map(_list_to_dict, l[1:]))))
    return dict(list(map(_list_to_dict, l)))
    # # TODO: does it make sense to parse ints here?
    # print (l)
    # if isinstance(l, str) or l is None:
    #     return l
    # if len(l) == 2:
    #     return l
    # if len(l) == 1:
    #     return dict(l)
    # return { l[0]: dict(list(map(_list_to_dict, l[1:])))}
    # t = list(map(_list_to_dict, l))
    # print("t: %s" % t)
    # d = dict([t])
    # print ("d: %s" % d)
    # return d

def _postprocess_parsed(l, format):
    # TODO: check format: deep vs old-style vs dash; act accordingly
    if not isinstance(l[0], str):
        # Root node
        metadata = {}
        tree = None
        id = None
        try:
            while True:
                v = l.pop()
                if v[0] == 'ID':
                    id = v[1]
                elif v[0] == 'METADATA':
                    metadata = _list_to_dict(v[1:])
                else:
                    if tree:
                        raise ParseError("Too many children of root node "
                                         "(or label-less node)")
                    tree = v
        except IndexError:
            pass
        try:
            return Root(id, _postprocess_parsed(tree, format), metadata)
        except ParseError as e:
            print("error in id: %s" % id)
            raise e
    if len(l) < 2:
        raise ParseError("malformed tree: node has too few children: %s" % l)
    if isinstance(l[1], str):
        # Simple leaf
        if len(l) != 2:
            raise ParseError("malformed tree: leaf has too many children: %s"
                             % l)
        m = {}
        label = l[0]
        text = l[1]
        # TODO: move this check to a utility fn
        if l[1].split("-")[0] in ["*T*", "*ICH*", "*CL*", "*"]:
            text, idx_type, index = lovett.util.label_and_index(text)
            if index is not None:
                m['INDEX'] = index
                m['IDX-TYPE'] = idx_type
        else:
            label, idx_type, index = lovett.util.label_and_index(label)
            if index is not None:
                m['INDEX'] = index
                m['IDX-TYPE'] = idx_type
        if format == "dash" and not (label.startswith("CODE") or
                                     label.startswith("CODING")):
            s = text.split("-")
            if len(s) > 1:
                m['LEMMA'] = s.pop()
                text = "-".join(s)
        return Leaf(label, text, m)
    if len(l) == 3 and sorted(map(lambda x: x[0], l[1:])) == ['METADATA',
                                                              'ORTHO']:
        # Deep format leaf
        label = l[0]
        o, m = l[1], l[2]
        if o[0] == 'METADATA':
            o, m = m, o
        return Leaf(label, o, _list_to_dict(m[1:]))
    # Regular node
    m = next((x for x in l[1:] if x[0] == 'METADATA'), None)
    if m is not None:
        m = _list_to_dict(m[1:])
    else:
        m = {}
    label, idx_type, index = lovett.util.label_and_index(l[0])
    if index is not None:
        m['INDEX'] = index
        m['IDX-TYPE'] = idx_type
    return NonTerminal(label, map(lambda x: _postprocess_parsed(x, format),
                                  l[1:]),
                       m)

# TODO: better parse errors
def parse(string, format="old-style"):
    stack = []
    stream = _tokenize(string)
    r = None
    for token in stream:
        if token == '(':
            stack.append([])
        elif token == ')':
            r = stack.pop()
            try:
                stack[len(stack) - 1].append(r)
            except IndexError:
                # the final closing bracket
                break
        else:
            try:
                stack[len(stack) - 1].append(token)
            except Exception:
                raise ParseError("error with stack: %s" % stack)

    n = next(stream, None)
    if n is not None:
        raise ParseError("unmatched closing bracket: %s" % r)
    if not len(stack) == 0:
        raise ParseError("unmatched opening bracket: %s" % stack)

    return r and _postprocess_parsed(r, format)

def parse_xml(string):
    xml = etree.fromstring(string)
    if not xml.tag == "sent":
        # TODO: XMLParseError subclass
        # TODO: sent has more than one child
        raise ParseError("not a sentence")
    d = dict(xml.items())
    id = d.pop('ID')
    return Root(id, parse_xml_nt(xml[0]), d)

def parse_xml_dispatch(elem):
    if elem.tag == "node":
        return parse_xml_nt(elem)
    elif elem.tag == "leaf":
        return parse_xml_leaf(elem)
    else:
        raise ParseError("unknown tag %s" % elem.tag)

def parse_xml_nt(elem):
    if not elem.tag == "node":
        raise ParseError("not a node")
    d = dict(elem.items())
    label = d.pop('label')
    return NonTerminal(label, [parse_xml_dispatch(child) for child in elem], d)

def parse_xml_leaf(elem):
    if not elem.tag == "leaf":
        raise ParseError("not a leaf")
    d = dict(elem.items())
    label = d.pop('label')
    return Leaf(label, elem.text, d)
