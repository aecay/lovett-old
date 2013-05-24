from __future__ import unicode_literals

import collections
from functools import total_ordering

import lovett.util

TaggedWord = collections.namedtuple("TaggedWord", ['pos', 'word'])

class Tree(collections.abc.Hashable):
    # TODO: use __getattr__ to pass to metadata dict?
    def __init__(self, label):
        self.parent = None
        self._label = label

    def __hash__(self):
        return hash(str(self._key_tuple()))

    def __eq__(self, other):
        return self._key_tuple() == other._key_tuple()

    def _key_tuple(self):
        raise NotImplementedError

    @property
    def label(self):
        return self._label
    @label.setter
    def label(self, new):
        new = new.strip()
        if new == '':
            raise ValueError('Nodes cannot have an empty label.')
        self._label = new

    @property
    def parent_index(self):
        if self.parent is None:
            return None
        for i, child in enumerate(self.parent):
            if child is self:
                return i
        raise ValueError("Tree not contained in its parent")
    @property
    def left_sibling(self):
        parent_index = self.parent_index
        if self.parent and parent_index > 0:
            return self.parent[parent_index - 1]
        # We don't have a parent
        return None
    @property
    def right_sibling(self):
        parent_index = self.parent_index
        if self.parent and parent_index < len(self.parent) - 1:
            return self.parent[parent_index + 1]
        # We don't have a parent
        return None

    @property
    def root(self):
        root = self
        while root.parent is not None:
            root = root.parent
        return root

class Leaf(Tree):
    # TODO: implement dict interface passthrough to metadata?
    def __init__(self, label, text, metadata = None):
        super(Leaf, self).__init__(label)
        self.text = text
        # TODO: we might want to parse metadata
        self.metadata = metadata or {}
        # TODO: lemma

    def __str__(self, indent = 0):
        # TODO: handle metadata, lemma
        return ''.join(['(', self.label, ' ', self.text, ')'])

    def __repr__(self):
        return "Leaf(%s, %s, metadata=%r)" % (self.label, self.text,
                                              self.metadata)

    def _key_tuple(self):
        return ("leaf", self.label, self.text, self.metadata)

class NonTerminal(Tree,collections.MutableSequence):
    # TODO: implement dict interface passthrough to metadata? -- complicated,
    # since this is already a different type of sequence
    def __init__(self, label, children, metadata = None):
        # TODO: use *args magic to not need the list brax around children?
        super(NonTerminal, self).__init__(label)
        # coerce to a list; we don't want any generators to sneak in
        self._children = list(children)
        # TODO: we might want to parse metadata
        self.metadata = metadata or {}
        for child in self._children:
            child.parent = self

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
        if isinstance(index, (int, slice)):
            return self._children[index]
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    # For MutableSequence
    def __setitem__(self, index, value):
        if isinstance(index, (int, slice)):
            value.parent = self
            self._children[index] = value
            # TODO: what should be returned???
            return self._children[index]
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def __delitem__(self, index):
        if isinstance(index, (int, slice)):
            # TODO: is there a better way to do this?
            if isinstance(index, int):
                self._children[index].parent = None
            else:
                for child in self._children[index]:
                    child.parent = None
            # TODO: should something be returned?
            del self._children[index]
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def insert(self, index, value):
        if isinstance(index, (int, slice)):
            value.parent = self
            return self._children.insert(index, value)
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def _key_tuple(self):
        return ("nonterminal", self.label, self._children, self.metadata)

    ### Properties
    @property
    def children(self):
        return self.__iter__()

    @property
    def leaves(self):
        for child in self:
            if isinstance(child, NonTerminal):
                yield from child
            else:
                yield child

    @property
    def height(self):
        max_child_height = 0
        for child in self:
            if isinstance(child, NonTerminal):
                max_child_height = max(max_child_height, child.height())
            else:
                max_child_height = max(max_child_height, 1)
        return 1+ max_child_height

    @property
    def subtrees(self):
        yield self
        for child in self:
            if hasattr(child, 'subtrees'):
                yield from child.subtrees
            else:
                yield child

    @property
    def pos(self):
        # TODO: do we need this?
        yield from (TaggedWord(x.label, x.text) for x in self if isinstance(x, Leaf))

    # Copying -- use copy.copy and copy.deepcopy

    # TODO: use our utility fns
    def __repr__(self):
        childstr = ", ".join(repr(c) for c in self)
        return '%s(%s, [%s], metadata=%r)' % (type(self).__name__, self.label,
                                              childstr, self.metadata)

    def __str__(self, indent = 0):
        s = "(%s " % self.label
        l = len(s)
        leaves = ("\n" + " " * (indent + l)).join(
            map(lambda x: x.__str__(indent + l), self))
        metadata = ""
        if self.metadata != {}:
            metadata = "\n" + " " * (indent + l) + \
                       lovett.util.metadata_str(self.metadata,
                                                "METADATA",
                                                indent + l)
        return "".join([s, leaves, metadata, ")"])

class Root(NonTerminal):
    def __init__(self, id, tree, metadata = None):
        super(Root, self).__init__('', [tree])
        self.id = id
        self.metadata = metadata or {}

    def _key_tuple(self):
        return ("root", self.id, self[0], self.metadata)

    def __str__(self, indent = 0):
        s = super(Root, self).__str__(indent)
        if self.id is not None:
            s = s[0:len(s)-1] + "\n  (ID " + self.id + "))"
        return s
    def __repr__(self):
        s = super(Root, self).__repr__()
        s = "Root(" + s[7:len(s)] # get rid of the empty label
        return s

    @property
    def parent(self):
        return None
    @parent.setter
    def parent(self, new):
        if new is not None:
            raise ValueError('Cannot insert a Root into another tree.')

    def insert(self, x, index):
        raise ValueError("Cannot insert into a Root")
    def __delitem__(self, index):
        raise ValueError("Cannot delete from a Root")
    def __setitem__(self, index, value):
        if index != 0:
            raise ValueError("Cannot only set item at index 0 of a root (given: %s)",
                             index)
        super(Root, self).__setitem__(index, value)

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

def _postprocess_parsed(l):
    # TODO: check format
    ln = len(l)
    if ln == 2 and isinstance(l[1], str):
        # Simple leaf
        return Leaf(l[0], l[1])
    if ln == 3 and sorted(map(lambda x: x[0], l[1:])) == ['METADATA', 'ORTHO']:
        # Deep format leaf
        label = l[0]
        o, m = l[1], l[2]
        if o[0] == 'METADATA':
            o, m = m, o
        return Leaf(leaf, o, _list_to_dict(m[1:]))
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
                        raise ValueError("Too many children of root node (or label-less node)")
                    tree = v
        except IndexError:
            pass
        return Root(id, _postprocess_parsed(tree), metadata)
    # Regular node
    m = next((x for x in l[1:] if x[0] == 'METADATA'), None)
    if m is not None:
        m = _list_to_dict(m[1:])
    return NonTerminal(l[0], map(_postprocess_parsed, l[1:]), m)

# TODO: better parse errors
def parse(string):
    stack = []
    stream = _tokenize(string)
    for token in stream:
        if token == '(':
            stack.append([])
        elif token == ')':
            r = stack.pop()
            try:
                stack[len(stack)-1].append(r)
            except IndexError:
                # the final closing bracket
                break
        else:
            stack[len(stack)-1].append(token)

    n = next(stream, None)
    if n is not None:
        raise ParseError("unmatched closing bracket")
    if not len(stack) == 0:
        raise ParseError("unmatched opening bracket")

    return _postprocess_parsed(r)
