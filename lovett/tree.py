# This Python file uses the following encoding: utf-8

import re
import string
import util

__docformat__ = "restructuredtext en"


# These two functions are part of an abortive attempt to make parsing trees
# faster.
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

# TODO: eliminate
from nltk.util import slice_bounds

######################################################################
## Trees
######################################################################

class Tree(list):
    """A Tree represents a hierarchical grouping of leaves and subtrees.  For
    example, each constituent in a syntax tree is represented by a single
    Tree.

    A tree's children are encoded as a list of leaves and subtrees,
    where a leaf is a basic (non-tree) value; and a subtree is a
    nested Tree.

        >>> from nltk.tree import Tree
        >>> print Tree(1, [2, Tree(3, [4]), 5])
        (1 2 (3 4) 5)
        >>> vp = Tree('VP', [Tree('V', ['saw']),
        ...                  Tree('NP', ['him'])])
        >>> s = Tree('S', [Tree('NP', ['I']), vp])
        >>> print s
        (S (NP I) (VP (V saw) (NP him)))
        >>> print s[1]
        (VP (V saw) (NP him))
        >>> print s[1,1]
        (NP him)
        >>> t = Tree("(S (NP I) (VP (V saw) (NP him)))")
        >>> s == t
        True
        >>> t[1][1].node = "X"
        >>> print t
        (S (NP I) (VP (V saw) (X him)))
        >>> t[0], t[1,1] = t[1,1], t[0]
        >>> print t
        (S (X him) (VP (V saw) (NP I)))

    The length of a tree is the number of children it has.

        >>> len(t)
        2

    Any other properties that a Tree defines are known as node
    properties, and are used to add information about individual
    hierarchical groupings.  For example, syntax trees use a NODE
    property to label syntactic constituents with phrase tags, such as
    "NP" and "VP".

    Several Tree methods use "tree positions" to specify
    children or descendants of a tree.  Tree positions are defined as
    follows:

      - The tree position *i* specifies a Tree's *i*\ th child.
      - The tree position ``()`` specifies the Tree itself.
      - If *p* is the tree position of descendant *d*, then
        *p+i* specifies the *i*\ th child of *d*.

    I.e., every tree position is either a single index *i*,
    specifying ``tree[i]``; or a sequence *i1, i2, ..., iN*,
    specifying ``tree[i1][i2]...[iN]``.

    Construct a new tree.  This constructor can be called in one
    of two ways:

    - ``Tree(node, children)`` constructs a new tree with the
        specified node value and list of children.

    - ``Tree(s)`` constructs a new tree by parsing the string ``s``.
        It is equivalent to calling the class method ``Tree.parse(s)``.

    """
    def __init__(self, node_or_str, children=None):
        if children is None:
            if not isinstance(node_or_str, basestring):
                raise TypeError("%s: Expected a node value and child list "
                                "or a single string" % type(self).__name__)
            tree = type(self).parse(node_or_str)
            list.__init__(self, tree)
            self.node = tree.node
        elif isinstance(children, basestring):
            raise TypeError("%s() argument 2 should be a list, not a "
                            "string" % type(self).__name__)
        else:
            list.__init__(self, children)
            self.node = node_or_str

    #////////////////////////////////////////////////////////////
    # Comparison operators
    #////////////////////////////////////////////////////////////

    def __eq__(self, other):
        if not isinstance(other, Tree): return False
        return self.node == other.node and list.__eq__(self, other)
    def __ne__(self, other):
        return not (self == other)
    def __lt__(self, other):
        if not isinstance(other, Tree): return False
        return self.node < other.node or list.__lt__(self, other)
    def __le__(self, other):
        if not isinstance(other, Tree): return False
        return self.node <= other.node or list.__le__(self, other)
    def __gt__(self, other):
        if not isinstance(other, Tree): return True
        return self.node > other.node or list.__gt__(self, other)
    def __ge__(self, other):
        if not isinstance(other, Tree): return False
        return self.node >= other.node or list.__ge__(self, other)

    #////////////////////////////////////////////////////////////
    # Disabled list operations
    #////////////////////////////////////////////////////////////

    def __mul__(self, v):
        raise TypeError('Tree does not support multiplication')
    def __rmul__(self, v):
        raise TypeError('Tree does not support multiplication')
    def __add__(self, v):
        raise TypeError('Tree does not support addition')
    def __radd__(self, v):
        raise TypeError('Tree does not support addition')

    #////////////////////////////////////////////////////////////
    # Indexing (with support for tree positions)
    #////////////////////////////////////////////////////////////

    def __getitem__(self, index):
        if isinstance(index, (int, slice)):
            return list.__getitem__(self, index)
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

    def __setitem__(self, index, value):
        if isinstance(index, (int, slice)):
            return list.__setitem__(self, index, value)
        elif isinstance(index, (list, tuple)):
            if len(index) == 0:
                raise IndexError('The tree position () may not be '
                                 'assigned to.')
            elif len(index) == 1:
                self[index[0]] = value
            else:
                self[index[0]][index[1:]] = value
        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def __delitem__(self, index):
        if isinstance(index, (int, slice)):
            return list.__delitem__(self, index)
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

    #////////////////////////////////////////////////////////////
    # Basic tree operations
    #////////////////////////////////////////////////////////////

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
                leaves.extend(child.leaves())
            else:
                leaves.append(child)
        return leaves

    def flatten(self):
        """
        Return a flat version of the tree, with all non-root non-terminals removed.

            >>> t = Tree("(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))")
            >>> print t.flatten()
            (S the dog chased the cat)

        :return: a tree consisting of this tree's root connected directly to
            its leaves, omitting all intervening non-terminal nodes.
        :rtype: Tree
        """
        return Tree(self.node, self.leaves())

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

    def leaf_treeposition(self, index):
        """
        :return: The tree position of the ``index``-th leaf in this
            tree.  I.e., if ``tp=self.leaf_treeposition(i)``, then
            ``self[tp]==self.leaves()[i]``.

        :raise IndexError: If this tree contains fewer than ``index+1``
            leaves, or if ``index<0``.
        """
        if index < 0: raise IndexError('index must be non-negative')

        stack = [(self, ())]
        while stack:
            value, treepos = stack.pop()
            if not isinstance(value, Tree):
                if index == 0: return treepos
                else: index -= 1
            else:
                for i in range(len(value)-1, -1, -1):
                    stack.append( (value[i], treepos+(i,)) )

        raise IndexError('index must be less than or equal to len(self)')

    def treeposition_spanning_leaves(self, start, end):
        """
        :return: The tree position of the lowest descendant of this
            tree that dominates ``self.leaves()[start:end]``.
        :raise ValueError: if ``end <= start``
        """
        if end <= start:
            raise ValueError('end must be greater than start')
        # Find the tree positions of the start & end leaves, and
        # take the longest common subsequence.
        start_treepos = self.leaf_treeposition(start)
        end_treepos = self.leaf_treeposition(end-1)
        # Find the first index where they mismatch:
        for i in range(len(start_treepos)):
            if i == len(end_treepos) or start_treepos[i] != end_treepos[i]:
                return start_treepos[:i]
        return start_treepos

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

    def copy(self, deep=False):
        if not deep: return type(self)(self.node, self)
        else: return type(self).convert(self)

    def _frozen_class(self): return ImmutableTree
    def freeze(self, leaf_freezer=None):
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
        if not isinstance(brackets, basestring) or len(brackets) != 2:
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

    def __repr__(self):
        childstr = ", ".join(repr(c) for c in self)
        return '%s(%r, [%s])' % (type(self).__name__, self.node, childstr)

    def __unicode__(self, indent = 0):
        if len(self) == 1 and isinstance(self[0], basestring):
            # This is a leaf node
            # TODO: python3 compat of isinstance, string formatting
            return u"(%s %s)" % (unicode(self.node), unicode(self[0]))
        else:
            s = u"(%s " % (unicode(self.node))
            l = len(s)
            # lstrip is to whack the initial newline+spaces
            leaves = (u"\n" + u" " * (indent + l)).join(map(lambda x: x.__unicode__(indent + l), self))
            return u"%s%s%s" % (s, leaves, u")")

    def __str__(self, indent = 0):
        return str(self.__unicode__(indent))

class ImmutableTree(Tree):
    def __init__(self, node_or_str, children=None):
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

    def __init__(self, node_or_str, children=None):
        super(ParentedTree, self).__init__(node_or_str, children)
        self._parent = None
        for i, child in enumerate(self):
            if isinstance(child, Tree):
                if children is None:
                    # If children is None, the tree is parsed from node_or_str.
                    # After parsing, the parent of the immediate children
                    # will point to an intermediate tree, not self.
                    # We fix this by brute force:
                    child._parent = None
                self._setparent(child, i)

    def _frozen_class(self): return ImmutableParentedTree

    #////////////////////////////////////////////////////////////
    # Parent management
    #////////////////////////////////////////////////////////////

    def _delparent(self, child, index):
        # Sanity checks
        assert isinstance(child, ParentedTree)
        assert self[index] is child
        assert child._parent is self

        # Delete child's parent pointer.
        child._parent = None

    def _setparent(self, child, index, dry_run=False):
        # If the child's type is incorrect, then complain.
        if not isinstance(child, ParentedTree):
            raise TypeError('Can not insert a non-ParentedTree '+
                            'into a ParentedTree')

        # If child already has a parent, then complain.
        if child._parent is not None:
            raise ValueError('Can not insert a subtree that already '
                             'has a parent.')

        # Set child's parent pointer & index.
        if not dry_run:
            child._parent = self

    #////////////////////////////////////////////////////////////
    # Methods that add/remove children
    #////////////////////////////////////////////////////////////
    # Every method that adds or removes a child must make
    # appropriate calls to _setparent() and _delparent().

    def __delitem__(self, index):
        # del ptree[start:stop]
        if isinstance(index, slice):
            start, stop, step = util.slice_bounds(self, index, allow_step=True)
            # Clear all the children pointers.
            for i in xrange(start, stop, step):
                if isinstance(self[i], Tree):
                    self._delparent(self[i], i)
            # Delete the children from our child list.
            super(ParentedTree, self).__delitem__(index)

        # del ptree[i]
        elif isinstance(index, int):
            if index < 0: index += len(self)
            if index < 0: raise IndexError('index out of range')
            # Clear the child's parent pointer.
            if isinstance(self[index], Tree):
                self._delparent(self[index], index)
            # Remove the child from our child list.
            super(ParentedTree, self).__delitem__(index)

        elif isinstance(index, (list, tuple)):
            # del ptree[()]
            if len(index) == 0:
                raise IndexError('The tree position () may not be deleted.')
            # del ptree[(i,)]
            elif len(index) == 1:
                del self[index[0]]
            # del ptree[i1, i2, i3]
            else:
                del self[index[0]][index[1:]]

        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def __setitem__(self, index, value):
        # ptree[start:stop] = value
        if isinstance(index, slice):
            start, stop, step = util.slice_bounds(self, index, allow_step=True)
            # make a copy of value, in case it's an iterator
            if not isinstance(value, (list, tuple)):
                value = list(value)
            # Check for any error conditions, so we can avoid ending
            # up in an inconsistent state if an error does occur.
            for i, child in enumerate(value):
                if isinstance(child, Tree):
                    self._setparent(child, start + i*step, dry_run=True)
            # clear the child pointers of all parents we're removing
            for i in xrange(start, stop, step):
                if isinstance(self[i], Tree):
                    self._delparent(self[i], i)
            # set the child pointers of the new children.  We do this
            # after clearing *all* child pointers, in case we're e.g.
            # reversing the elements in a tree.
            for i, child in enumerate(value):
                if isinstance(child, Tree):
                    self._setparent(child, start + i*step)
            # finally, update the content of the child list itself.
            super(ParentedTree, self).__setitem__(index, value)

        # ptree[i] = value
        elif isinstance(index, int):
            if index < 0: index += len(self)
            if index < 0: raise IndexError('index out of range')
            # if the value is not changing, do nothing.
            if value is self[index]:
                return
            # Set the new child's parent pointer.
            if isinstance(value, Tree):
                self._setparent(value, index)
            # Remove the old child's parent pointer
            if isinstance(self[index], Tree):
                self._delparent(self[index], index)
            # Update our child list.
            super(ParentedTree, self).__setitem__(index, value)

        elif isinstance(index, (list, tuple)):
            # ptree[()] = value
            if len(index) == 0:
                raise IndexError('The tree position () may not be assigned to.')
            # ptree[(i,)] = value
            elif len(index) == 1:
                self[index[0]] = value
            # ptree[i1, i2, i3] = value
            else:
                self[index[0]][index[1:]] = value

        else:
            raise TypeError("%s indices must be integers, not %s" %
                            (type(self).__name__, type(index).__name__))

    def append(self, child):
        if isinstance(child, Tree):
            self._setparent(child, len(self))
        super(ParentedTree, self).append(child)

    def extend(self, children):
        for child in children:
            if isinstance(child, Tree):
                self._setparent(child, len(self))
            super(ParentedTree, self).append(child)

    def insert(self, index, child):
        # Handle negative indexes.  Note that if index < -len(self),
        # we do *not* raise an IndexError, unlike __getitem__.  This
        # is done for consistency with list.__getitem__ and list.index.
        if index < 0: index += len(self)
        if index < 0: index = 0
        # Set the child's parent, and update our child list.
        if isinstance(child, Tree):
            self._setparent(child, index)
        super(ParentedTree, self).insert(index, child)

    def pop(self, index=-1):
        if index < 0: index += len(self)
        if index < 0: raise IndexError('index out of range')
        if isinstance(self[index], Tree):
            self._delparent(self[index], index)
        return super(ParentedTree, self).pop(index)

    # n.b.: like `list`, this is done by equality, not identity!
    # To remove a specific child, use del ptree[i].
    def remove(self, child):
        index = self.index(child)
        if isinstance(self[index], Tree):
            self._delparent(self[index], index)
        super(ParentedTree, self).remove(child)

    # We need to implement __getslice__ and friends, even though
    # they're deprecated, because otherwise list.__getslice__ will get
    # called (since we're subclassing from list).  Just delegate to
    # __getitem__ etc., but use max(0, start) and max(0, stop) because
    # because negative indices are already handled *before*
    # __getslice__ is called; and we don't want to double-count them.
    if hasattr(list, '__getslice__'):
        def __getslice__(self, start, stop):
            return self.__getitem__(slice(max(0, start), max(0, stop)))
        def __delslice__(self, start, stop):
            return self.__delitem__(slice(max(0, start), max(0, stop)))
        def __setslice__(self, start, stop, value):
            return self.__setitem__(slice(max(0, start), max(0, stop)), value)

    #/////////////////////////////////////////////////////////////////
    # Properties
    #/////////////////////////////////////////////////////////////////

    @property
    def parent(self):
        """The parent of this tree, or None if it has no parent."""
        return self._parent

    @property
    def parent_index(self):
        """
        The index of this tree in its parent.  I.e.,
        ``ptree.parent[ptree.parent_index] is ptree``.  Note that
        ``ptree.parent_index`` is not necessarily equal to
        ``ptree.parent.index(ptree)``, since the ``index()`` method
        returns the first child that is equal to its argument.
        """
        if self._parent is None: return None
        for i, child in enumerate(self._parent):
            if child is self: return i
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
        if self.parent is None: return ()
        else: return self.parent.treeposition + (self.parent_index,)


class ImmutableParentedTree(ImmutableTree, ParentedTree):
    pass

##########

class LovettTree(ParentedTree):
    """A class that wraps a ``nltk.tree.ParentedTree``.

    Currently it does not do much.

    """
    pass

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
