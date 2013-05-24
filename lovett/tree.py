# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import collections
import re
import string

import lovett.util

from functools import total_ordering

__docformat__ = "restructuredtext en"


# These two functions are part of an abortive attempt to make parsing trees
# faster.

# TODO: try using string indices?
def nextToken(s):
    s = s.lstrip()
    if s == "":
        raise Exception("ran out of input")
    if s[0] in "()":
        return s[0], s[1:]
    else:
        i = 1
        while s[i] not in " )\n\t":
            i += 1
        return s[0:i], s[i:]

def parseTree(s):
    stack = []
    while True:
        t, s = nextToken(s)
        if t == "(":
            n, s = nextToken(s)
            if n == "(":
                s = n + s
                n = ""
            stack.append(LovettTree(n, []))
        elif t == ")":
            p = stack.pop()
            if len(stack) == 0:
                if s.strip() == "":
                    return p
                else:
                    raise Exception("extra input: %s" % s)
            stack[-1].append(p)
        else:
            stack[-1].append(t)


##########

# Natural Language Toolkit: Text Trees
#
# Copyright (C) 2001-2012 NLTK Project
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
#         Steven Bird <sb@csse.unimelb.edu.au>
#         Peter Ljunglöf <peter.ljunglof@gu.se>
#         Nathan Bodenstab <bodenstab@cslu.ogi.edu> (tree transforms)
# URL: <http://www.nltk.org/>
# TODO
# For license information, see LICENSE.TXT

######################################################################
## Trees
######################################################################

# TODO: make an abstract base class, have Leaf and Tree inherit from it
class Leaf(object):
    """TODO"""
    def __init__(self, node, label):
        self.label = label
        self._node = node

@total_ordering
class Tree(collections.MutableSequence):
    """foo.  TODO

    """
    def __init__(self, node, children):
        if node is None or children is None:
            raise TypeError("Two arguments required to create %s" % self.__name__)
        if not isinstance(node, str):
            raise TypeError("First argument to initialize %s should be a string" %
                            self.__name__)
        if not isinstance(children, list):
            raise TypeError("Second argument to initialize %s should be list-like" %
                            self.__name__)

        self._node = node
        self._children = children

    # Basic Properties
    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, val):
        self._node = val

    # TODO: is a generator right here?
    @property
    def children(self):
        for i in self:
            yield i

    # Abstract methods

    # For Container
    def __contains__(self, obj):
        return self._children.__contains__(obj)

    # For Iterable
    def __iter__(self):
        return self._children.__iter__()

    def next(self):
        return self._children.next()

    # For total_ordering
    def __eq__(self, other):
        if not isinstance(other, Tree):
            return False
        return self.node == other.node and self._children == other._children
    def __lt__(self, other):
        if not isinstance(other, Tree):
            return False
        return self.node < other.node or super(Tree,self).__lt__(self, other)

    # For Sized
    def __len__(self):
        return len(self._children)

    # For Sequence
    def __getitem__(self, index):
        if isinstance(index, (int, slice)):
            return self._children[index]
        elif isinstance(index, (list, tuple)):
            if len(index) == 0:
                return self
            elif len(index) == 1:
                return self[index[0]]
            else:
                return self[index[0]][index[1:]]
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    # For MutableSequence
    def __setitem__(self, index, value):
        if isinstance(index, (int, slice)):
            self._children[index] = value
            # TODO: what should be returned???
            return self._children[index]
        elif isinstance(index, (list, tuple)):
            if len(index) == 0:
                raise IndexError('The tree position () may not be assigned to.')
            elif len(index) == 1:
                self[index[0]] = value
            else:
                self[index[0]][index[1:]] = value
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def __delitem__(self, index):
        if isinstance(index, (int, slice)):
            # TODO: should something be returned?
            del self._children[index]
        elif isinstance(index, (list, tuple)):
            if len(index) == 0:
                raise IndexError('The tree position () may not be deleted.')
            elif len(index) == 1:
                del self[index[0]]
            else:
                del self[index[0]][index[1:]]
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def insert(self, index, value):
        if isinstance(index, (int, slice)):
            return self._children.insert(index, value)
        elif isinstance(index, (list, tuple)):
            if len(index) == 0:
                raise IndexError('The tree position () may not be inserted at.')
            elif len(index) == 1:
                self.insert(index[0], value)
            else:
                self[index[0]].insert(index[1:], value)
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    # Derived properties and methods

    # TODO: convert to generator
    @property
    def leaves(self):
        """
        Return the leaves of the tree.

            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
            >>> t.leaves()
            ['the', 'dog', 'chased', 'the', 'cat']

        :return: a list containing this tree's leaves.
            The order reflects the order of the
            leaves in the tree's hierarchical structure.
        :rtype: list
        """
        leaves = []
        for child in self:
            if isinstance(child, Tree):
                leaves.extend(child.leaves)
            else:
                leaves.append(child)
        return leaves

    @property
    def height(self):
        """
        Return the height of the tree.

            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
            >>> t.height()
            5
            >>> print t[0,0]
            (D the)
            >>> t[0,0].height()
            2

        :return: The height of this tree.  The height of a tree
            containing no children is 1; the height of a tree
            containing only leaves is 2; and the height of any other
            tree is one plus the maximum of its children's
            heights.
        :rtype: int
        """
        max_child_height = 0
        for child in self:
            if isinstance(child, Tree):
                max_child_height = max(max_child_height, child.height())
            else:
                max_child_height = max(max_child_height, 1)
        return 1 + max_child_height

    def treepositions(self, order='preorder'):
        """
            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
        >>> t.treepositions() # doctest: +ELLIPSIS
            [(), (0,), (0, 0), (0, 0, 0), (0, 1), (0, 1, 0), (1,), (1, 0), (1, 0, 0), ...]
            >>> for pos in t.treepositions('leaves'):
            ...     t[pos] = t[pos][::-1].upper()
            >>> print t
            (S (NP (D EHT) (N GOD)) (VP (V DESAHC) (NP (D EHT) (N TAC))))

        :param order: One of: ``preorder``, ``postorder``, ``bothorder``,
            ``leaves``.
        """
        positions = []
        if order in ('preorder', 'bothorder'): positions.append( () )
        for i, child in enumerate(self):
            if isinstance(child, Tree):
                childpos = child.treepositions(order)
                positions.extend((i,)+p for p in childpos)
            else:
                positions.append( (i,) )
        if order in ('postorder', 'bothorder'): positions.append( () )
        return positions

    # TODO: remove filter?
    def subtrees(self, filter=None):
        """
        Generate all the subtrees of this tree, optionally restricted
        to trees matching the filter function.

            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
            >>> for s in t.subtrees(lambda t: t.height() == 2):
            ...     print s
            (D the)
            (N dog)
            (V chased)
            (D the)
            (N cat)

        :type filter: function
        :param filter: the function to filter all local trees
        """
        if not filter or filter(self):
            yield self
        for child in self:
            if isinstance(child, Tree):
                for subtree in child.subtrees(filter):
                    yield subtree

    def pos(self):
        """
        Return a sequence of pos-tagged words extracted from the tree.

            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
            >>> t.pos()
            [('the', 'D'), ('dog', 'N'), ('chased', 'V'), ('the', 'D'), ('cat', 'N')]

        :return: a list of tuples containing leaves and pre-terminals (part-of-speech tags).
            The order reflects the order of the leaves in the tree's hierarchical structure.
        :rtype: list(tuple)
        """
        pos = []
        for child in self:
            if isinstance(child, Tree):
                pos.extend(child.pos())
            else:
                pos.append((child, self.node))
        return pos

    #////////////////////////////////////////////////////////////
    # Convert, copy
    #////////////////////////////////////////////////////////////

    @classmethod
    def convert(cls, tree):
        """
        Convert a tree between different subtypes of Tree.  ``cls`` determines
        which class will be used to encode the new tree.

        :type tree: Tree
        :param tree: The tree that should be converted.
        :return: The new Tree.
        """
        if isinstance(tree, Tree):
            children = [cls.convert(child) for child in tree]
            return cls(tree.node, children)
        else:
            return tree

    def copy(self, deep = False):
        if not deep:
            return type(self)(self.node, self)
        else:
            return type(self).convert(self)

    def _frozen_class(self):
        return ImmutableTree
    def freeze(self, leaf_freezer = None):
        frozen_class = self._frozen_class()
        if leaf_freezer is None:
            newcopy = frozen_class.convert(self)
        else:
            newcopy = self.copy(deep=True)
            for pos in newcopy.treepositions('leaves'):
                newcopy[pos] = leaf_freezer(newcopy[pos])
            newcopy = frozen_class.convert(newcopy)
        hash(newcopy) # Make sure the leaves are hashable.
        return newcopy

    #////////////////////////////////////////////////////////////
    # Parsing
    #////////////////////////////////////////////////////////////

    @classmethod
    def parse(cls, s, brackets='()', parse_node=None, parse_leaf=None,
              node_pattern=None, leaf_pattern=None,
              remove_empty_top_bracketing=False):
        """
        Parse a bracketed tree string and return the resulting tree.
        Trees are represented as nested brackettings, such as::

          (S (NP (NNP John)) (VP (V runs)))

        :type s: str
        :param s: The string to parse

        :type brackets: str (length=2)
        :param brackets: The bracket characters used to mark the
            beginning and end of trees and subtrees.

        :type parse_node: function
        :type parse_leaf: function
        :param parse_node, parse_leaf: If specified, these functions
            are applied to the substrings of ``s`` corresponding to
            nodes and leaves (respectively) to obtain the values for
            those nodes and leaves.  They should have the following
            signature:

               parse_node(str) -> value

            For example, these functions could be used to parse nodes
            and leaves whose values should be some type other than
            string (such as ``FeatStruct``).
            Note that by default, node strings and leaf strings are
            delimited by whitespace and brackets; to override this
            default, use the ``node_pattern`` and ``leaf_pattern``
            arguments.

        :type node_pattern: str
        :type leaf_pattern: str
        :param node_pattern, leaf_pattern: Regular expression patterns
            used to find node and leaf substrings in ``s``.  By
            default, both nodes patterns are defined to match any
            sequence of non-whitespace non-bracket characters.

        :type remove_empty_top_bracketing: bool
        :param remove_empty_top_bracketing: If the resulting tree has
            an empty node label, and is length one, then return its
            single child instead.  This is useful for treebank trees,
            which sometimes contain an extra level of bracketing.

        :return: A tree corresponding to the string representation ``s``.
            If this class method is called using a subclass of Tree,
            then it will return a tree of that type.
        :rtype: Tree
        """
        if not isinstance(brackets, str) or len(brackets) != 2:
            raise TypeError('brackets must be a length-2 string')
        if re.search('\s', brackets):
            raise TypeError('whitespace brackets not allowed')
        # Construct a regexp that will tokenize the string.
        open_b, close_b = brackets
        open_pattern, close_pattern = (re.escape(open_b), re.escape(close_b))
        if node_pattern is None:
            node_pattern = '[^\s%s%s]+' % (open_pattern, close_pattern)
        if leaf_pattern is None:
            leaf_pattern = '[^\s%s%s]+' % (open_pattern, close_pattern)
        token_re = re.compile('%s\s*(%s)?|%s|(%s)' % (
            open_pattern, node_pattern, close_pattern, leaf_pattern))
        # Walk through each token, updating a stack of trees.
        stack = [(None, [])] # list of (node, children) tuples
        for match in token_re.finditer(s):
            token = match.group()
            # Beginning of a tree/subtree
            if token[0] == open_b:
                if len(stack) == 1 and len(stack[0][1]) > 0:
                    cls._parse_error(s, match, 'end-of-string')
                node = token[1:].lstrip()
                if parse_node is not None: node = parse_node(node)
                stack.append((node, []))
            # End of a tree/subtree
            elif token == close_b:
                if len(stack) == 1:
                    if len(stack[0][1]) == 0:
                        cls._parse_error(s, match, open_b)
                    else:
                        cls._parse_error(s, match, 'end-of-string')
                node, children = stack.pop()
                stack[-1][1].append(cls(node, children))
            # Leaf node
            else:
                if len(stack) == 1:
                    cls._parse_error(s, match, open_b)
                if parse_leaf is not None: token = parse_leaf(token)
                stack[-1][1].append(token)

        # check that we got exactly one complete tree.
        if len(stack) > 1:
            cls._parse_error(s, 'end-of-string', close_b)
        elif len(stack[0][1]) == 0:
            cls._parse_error(s, 'end-of-string', open_b)
        else:
            assert stack[0][0] is None
            assert len(stack[0][1]) == 1
        tree = stack[0][1][0]

        # If the tree has an extra level with node='', then get rid of
        # it.  E.g.: "((S (NP ...) (VP ...)))"
        if remove_empty_top_bracketing and tree.node == '' and len(tree) == 1:
            tree = tree[0]
        # return the tree.
        return tree

    @classmethod
    def _parse_error(cls, s, match, expecting):
        """
        Display a friendly error message when parsing a tree string fails.
        :param s: The string we're parsing.
        :param match: regexp match of the problem token.
        :param expecting: what we expected to see instead.
        """
        # Construct a basic error message
        if match == 'end-of-string':
            pos, token = len(s), 'end-of-string'
        else:
            pos, token = match.start(), match.group()
        msg = '%s.parse(): expected %r but got %r\n%sat index %d.' % (
            cls.__name__, expecting, token, ' '*12, pos)
        # Add a display showing the error token itsels:
        s = s.replace('\n', ' ').replace('\t', ' ')
        offset = pos
        if len(s) > pos+10:
            s = s[:pos+10]+'...'
        if pos > 10:
            s = '...'+s[pos-10:]
            offset = 13
        msg += '\n%s"%s"\n%s^' % (' '*16, s, ' '*(17+offset))
        raise ValueError(msg)

    #////////////////////////////////////////////////////////////
    # Visualization & String Representation
    #////////////////////////////////////////////////////////////

    # TODO: use our utility fns
    def __repr__(self):
        childstr = ", ".join(repr(c) for c in self)
        return '%s(%r, [%s])' % (type(self).__name__, self.node, childstr)

    def __str__(self, indent = 0):
        if len(self) == 1 and isinstance(self[0], str):
            # This is a leaf node
            # TODO: python3 compat of isinstance, string formatting
            return u"(%s %s)" % (str(self.node), str(self[0]))
        else:
            s = u"(%s " % (str(self.node))
            l = len(s)
            # lstrip is to whack the initial newline+spaces
            leaves = (u"\n" + u" " * (indent + l)).join(map(lambda x: x.__str__(indent + l), self))
            return u"%s%s%s" % (s, leaves, u")")

class ImmutableTree(Tree,collections.Hashable):
    def __init__(self, node, children):
        super(ImmutableTree, self).__init__(node_or_str, children)
        # Precompute our hash value.  This ensures that we're really
        # immutable.  It also means we only have to calculate it once.
        try:
            self._hash = hash( (self.node, tuple(self)) )
        except (TypeError, ValueError):
            raise ValueError("%s: node value and children "
                             "must be immutable" % type(self).__name__)

    def __setitem__(self, index, value):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __setslice__(self, i, j, value):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __delitem__(self, index):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __delslice__(self, i, j):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __iadd__(self, other):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __imul__(self, other):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def append(self, v):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def extend(self, v):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def pop(self, v=None):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def remove(self, v):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def reverse(self):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def sort(self):
        raise ValueError('%s may not be modified' % type(self).__name__)
    def __hash__(self):
        return self._hash

    @property
    def node(self):
        """Get the node value"""
        return self._node

    @node.setter
    def node(self, value):
        """
        Set the node value.  This will only succeed the first time the
        node value is set, which should occur in ImmutableTree.__init__().
        """
        if hasattr(self, 'node'):
            raise ValueError('%s may not be modified' % type(self).__name__)
        self._node = value


######################################################################
## Parented trees
######################################################################

class ParentedTree(Tree):
    """A ``Tree`` that automatically maintains parent pointers for
    single-parented trees.  The following read-only property values
    are automatically updated whenever the structure of a parented
    tree is modified: ``parent``, ``parent_index``, ``left_sibling``,
    ``right_sibling``, ``root``, ``treeposition``.

    Each ``ParentedTree`` may have at most one parent.  In particular,
    subtrees may not be shared.  Any attempt to reuse a single
    ``ParentedTree`` as a child of more than one parent (or as multiple
    children of the same parent) will cause a ``ValueError`` exception to be
    raised.

    """

    def __init__(self, node, children):
        for index, child in enumerate(children):
            if isinstance(child, Tree) and not isinstance(child, ParentedTree):
                children[i] = child.convert(ParentedTree)
        super(ParentedTree, self).__init__(node, children)
        self._parent = None
        for i, child in enumerate(self):
            if isinstance(child, Tree):
                child.parent = self

    def _frozen_class(self):
        return ImmutableParentedTree

    #////////////////////////////////////////////////////////////
    # Methods that add/remove children
    #////////////////////////////////////////////////////////////
    # Every method that adds or removes a child must make
    # appropriate calls to _setparent() and _delparent().

    def __delitem__(self, index):
        for child in self[index]:
            if isinstance(child, Tree):
                child.parent = None
        super(ParentedTree, self).__delitem__(index)

    def __setitem__(self, index, value):
        super(ParentedTree,self).__setitem__(index, value)
        for child in self:
            if isinstance(child, Tree):
                child.parent = self

    def append(self, child):
        if isinstance(child, Tree):
            child.parent = self
        super(ParentedTree, self).append(child)

    def extend(self, children):
        for child in children:
            if isinstance(child, Tree):
                self._setparent(child, len(self))
            super(ParentedTree, self).append(child)

    def insert(self, index, child):
        if isinstance(child, Tree):
            child.parent = self
        super(ParentedTree, self).insert(index, child)

    def pop(self, index = -1):
        if index < 0:
            index += len(self)
        if index < 0:
            raise IndexError('index out of range')
        if isinstance(self[index], Tree):
            self[index].parent = None
        return super(ParentedTree, self).pop(index)

    # n.b.: like `list`, this is done by equality, not identity!
    # To remove a specific child, use del ptree[i].
    # TODO: get rid of this method?
    def remove(self, child):
        index = self.index(child)
        if isinstance(self[index], Tree):
            self[index].parent = None
        super(ParentedTree, self).remove(child)

    #/////////////////////////////////////////////////////////////////
    # Properties
    #/////////////////////////////////////////////////////////////////

    @property
    def parent(self):
        """The parent of this tree, or None if it has no parent."""
        return self._parent
    @parent.setter
    def parent(self, newparent):
        self._parent = newparent

    @property
    def parent_index(self):
        """
        The index of this tree in its parent.  I.e.,
        ``ptree.parent[ptree.parent_index] is ptree``.  Note that
        ``ptree.parent_index`` is not necessarily equal to
        ``ptree.parent.index(ptree)``, since the ``index()`` method
        returns the first child that is equal to its argument.
        """
        if self._parent is None:
            return None
        for i, child in enumerate(self._parent):
            if child is self:
                return i
        assert False, 'expected to find self in self._parent!'

    @property
    def left_sibling(self):
        """The left sibling of this tree, or None if it has none."""
        parent_index = self.parent_index
        if self._parent and parent_index > 0:
            return self._parent[parent_index-1]
        return None # no left sibling

    @property
    def right_sibling(self):
        """The right sibling of this tree, or None if it has none."""
        parent_index = self.parent_index
        if self._parent and parent_index < (len(self._parent)-1):
            return self._parent[parent_index+1]
        return None # no right sibling

    @property
    def root(self):
        """
        The root of this tree.  I.e., the unique ancestor of this tree
        whose parent is None.  If ``ptree.parent`` is None, then
        ``ptree`` is its own root.
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    @property
    def treeposition(self):
        """
        The tree position of this tree, relative to the root of the
        tree.  I.e., ``ptree.root[ptree.treeposition] is ptree``.
        """
        if self.parent is None:
            return ()
        else:
            return self.parent.treeposition + (self.parent_index,)


class ImmutableParentedTree(ImmutableTree, ParentedTree):
    pass

##########

class LovettTree(ParentedTree):
    """A class that wraps a ``nltk.tree.ParentedTree``.

    Currently it does not do much.

    """
    # def subtrees(self, filter=None):
    #     """Overridden version from ``nltk.tree.Tree``.  Uses ``hasattr``
    #     instead of ``isinstance`` for speed.

    #     TODO: is this actually slower?

    #     """
    #     if not filter or filter(self):
    #         yield self
    #     for child in self:
    #         if hasattr(child, "node"):
    #             for subtree in child.subtrees(filter):
    #                 yield subtree
    pass
