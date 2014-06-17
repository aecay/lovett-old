# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import collections
import re
import string

import lovett.util

from functools import total_ordering

__docformat__ = "restructuredtext en"

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
