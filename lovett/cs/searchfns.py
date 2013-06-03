import lovett.tree_new as T
import re
import lovett.util as util
import sys
import inspect
import random
import operator

from functools import reduce

__docformat__ = "restructuredtext en"

def public(f):  # pragma: no cover
    # Use a decorator to avoid retyping function/class names.

    # * Based on an idea by Duncan Booth:
    # http://groups.google.com/group/comp.lang.python/msg/11cbb03e09611b8a
    # * Improved via a suggestion by Dave Angel:
    # http://groups.google.com/group/comp.lang.python/msg/3d400fb22d8a42e1
    all = sys.modules[f.__module__].__dict__.setdefault('__all__', [])
    if f.__name__ not in all:  # Prevent duplicates if run from an IDE.
        all.append(f.__name__)
    return f

# Match functions

@public
class SearchFunction:
    """This class wraps a function for searching parse trees.  It
    overrides the (bitwise) ``&``, ``|``, and ``~`` operators (and, or, and
    not respectively) to allow Boolean combinations of search terms.

    TODO: calling and return conventions for such a function

    """
    def __init__(self, fn, arg="", full_str=None):
        self.fn = fn
        fn_str = fn.__name__[1:]
        self.fn_str = fn_str
        self.arg = arg
        self.full_str = full_str

    # is this the place to put the ignore logic?
    def __call__(self, arg):
        # TODO: memoize
        # This if statement is so that non-results percolate through a chained
        # function.
        if arg:
            # Handle lists, returned by sister() etc.  this is looking
            # ugly, as we also handle lists in the treetransformer class
            if isinstance(arg, list):
                # TODO: this branch appears never to get called.  It
                # looks like a bottleneck in performance, so verify this
                # and remove.
                raise Exception("isinstance in __call__, arg is %s" % arg)
                return map(self.fn, arg)
            else:
                return self.fn(arg)
        else:
            return arg

    # TODO: scoping rules for and and or...
    def __and__(self, other):
        def _and(t):
            res = self(t)
            if not res:
                return res
            else:
                return other(t)
        return SearchFunction(_and,
                              full_str="%s & %s" % (str(self), str(other)))

    def __or__(self, other):
        def _or(t):
            res = self(t)
            if res:
                return res
            else:
                return other(t)
        return SearchFunction(_or,
                              full_str="%s | %s" % (str(self), str(other)))

    def __invert__(self):
        def _not(t):
            if self(t):
                return None
            else:
                return t
            return _not
        return SearchFunction(_not, full_str="~%s" % str(self))

    def __str__(self):
        if self.full_str is not None:
            return self.full_str
        return "%s(%s)" % (self.fn_str, _get_arg_string(self.arg))

# TODO: add below methods to (subclass of) ParentedTree?

# Ignoring things
ignore_function = SearchFunction(lambda x: False, "")
# Because of mutual recursion with this and hasLabel, the actual value
# is filled in below
default_ignore_function = lambda x: False

# TODO: not working yet
def setIgnore(fn):
    global ignore_function
    old_ignore = ignore_function
    ignore_function = fn
    return old_ignore

def shouldIgnore(t):
    return ignore_function(t) or default_ignore_function(t)

# Access functions

# This translated from the access function names to search fn names, below
sister_fn_map = {
    'allLeftSisters'  : 'leftSister',
    'allRightSisters' : 'rightSister',
    'nextLeftSister'  : 'immLeftSister',
    'nextRightSister' : 'immRightSister',
    'allSisters'      : 'sister'
}
def allLeftSisters(t):
    res = []
    while t:
        t = t.left_sibling
        if t and not shouldIgnore(t):
            res.append(t)
    return res

def allRightSisters(t):
    res = []
    while t:
        t = t.right_sibling
        if t and not shouldIgnore(t):
            res.append(t)
    return res

def allSisters(t):
    # Damn methods that return None instead of self
    return (allLeftSisters(t) or []) + (allRightSisters(t) or [])

def nextLeftSister(t):
    res = None
    while not res and t:
        t = t.left_sibling
        if not shouldIgnore(t):
            res = t
    return [res]

def nextRightSister(t):
    res = None
    while not res and t:
        t = t.right_sibling
        if not shouldIgnore(t):
            res = t
    return [res]

def allDaughters(t):
    if not hasattr(t, '__iter__'):
        return t
    return [d for d in t if not shouldIgnore(d)]

# Utility functions

# Something which is dumb: not having an identity function in your
# standard library.
class Identity(object):
    # This must be a class, in order to have a __str__ method
    def __call__(self, arg):
        return arg

    def __str__(self):
        # TODO: this isn't idempotent, and doesn't play well with
        # multiprocessing
        return "lambda x: x"

identity = Identity()

def _get_arg_string(x):
    if isinstance(x, type(re.compile(""))):
        return "re.compile(%s)" % x.pattern
    if isinstance(x, StartsWith):
        return "StartsWith(%s)" % x
    if isinstance(x, type(lambda: None)):
        try:
            return inspect.getsourcelines(x)
        except OSError:
            # TODO: this is really crappy
            return "<function %s>" % random.random()
    return "'" + str(x) + "'"

# Search functions

# TODO: some of the if..then stuff below is pretty verbose.  Maybe (when
# we are sure it all works), we want to make it terser, perhaps by
# defining a function orNone(val1, val2), which gives None if not val1,
# otherwise val2.

# TODO: put these in their own module, separate those which move search
# and those which don't

# We used to match either on the node label or the string (leaf
# node). But strings aren't tree positions.  So we had split these
# cases.  The hasLeafLabel function returns the leaf node (immediate
# parent) for words.

# TODO: handle ignore
# TODO: NP=2 should give hasLabel("NP") -> True
@public
def hasLabel(label, exact=False):
    """Tests if a node has a given label.

    :param label: The label to test for.  If a string, the behavior is
        controlled by the ``exact`` argument.  If a regex, then it is
        matched against the node label of the tree.

    :param exact: Controls how to match a string against a label.
        ``True`` requires ``label`` to match exactly the entire label.
        ``False`` (the default) allows ``label`` to match a node with
        extra trailing dash tags.

    """
    def _hasLabel(t):
        to_match = ""
        if isinstance(t, T.Tree):
            to_match = t.label
        else:
            return None

        if hasattr(label, "match"):
            if label.match(to_match):
                return t
            else:
                return None
        else:
            exact_match = label == to_match
            if exact:
                if exact_match:
                    return t
                else:
                    return None
            else:
                # TODO: gapping indices with =
                if exact_match or \
                   to_match[slice(len(label) + 1)] == label + "-":
                    return t
                else:
                    return None
    return SearchFunction(_hasLabel, label)

class StartsWith:
    def __init__(self, string):
        self.string = string

    def match(self, to_match):
        return to_match.startswith(self.string)

@public
def startsWith(string):
    return StartsWith(string)

# TODO: handle ignore
# TODO: rename to hasText?
@public
def hasText(text):
    """Tests if a leaf node has the given text.

    No match is returned if the target node is not a leaf node.

    This is a low-level function, not intended for use by end users.
    (TODO: don't export it)

    :param label: the text to test against the node's text.  If a
        string, it is matched against the node's text exactly, or with
        trailing dash tags removed.

    """
    def _hasText(t):
        if isinstance(t, T.Leaf):
            if hasattr(text, "match"):
                if text.match(t.text):
                    return t
                else:
                    return None
            else:
                exact_match = text == t.text
                if exact_match:
                    return t
                else:
                    if t.text[slice(len(text) + 1)] == text + "-":
                        return t
                    else:
                        return None
        else:
            return None
    return SearchFunction(_hasText, text)

# default_ignore_function = hasLabel("CODE") | hasLabel("ID") # ...
@public
def hasLemma(lemma):
    """Tests if a node has the given lemma.

    :param lemma: The lemma to look for.  Can be a regular expression or
        a string (the latter is matched exactly against the lemma).

    """
    def _hasLemma(t):
        if not isinstance(t, T.Leaf):
            return None
        try:
            the_lemma = t.metadata['LEMMA']
        except KeyError:
            return None
        if hasattr(lemma, "match"):
            if lemma.match(the_lemma):
                return t
            else:
                return None
        else:
            if the_lemma == lemma:
                return t
            else:
                return None
    return SearchFunction(_hasLemma, lemma)

# TODO: make aware of different formats (deep, dash)
# is this redundant with hasLeafLabel?  Should this be called hasText?

# TODO: doesn't work with startswith and friends. should be refactored for new
# tree impl
@public
def hasWord(word):
    """Tests if a node has the given word (exact text).

    :param word: the text to look for.  Matched rigidly against the
        ur-text of the leaf node.  No match if the target node is not a
        leaf.

    """
    if hasattr(word, "pattern"):
        word = word.pattern
    else:
        word = re.escape(word)
    r = hasLeafLabel(re.compile("^(" + word + ")-"))
    r.fn_str = "hasWord"
    r.arg = word
    return r

@public
def hasDashTag(tag):
    """Tests if the given node has a dash tag.

    :param tag: the dash tag to look for.

    """
    r = hasLabel(re.compile(".*-" + tag + "(-|$)"))
    r.fn_str = "hasDashTag"
    r.arg = tag

@public
def hasDaughter(fn=identity):
    """Tests if a node has a daughter matching a predicate.  If so, the
    original node (not the daughter) is returned.  Matching only looks
    at immediate daughters -- to extend further down the tree, see the
    `deep` function.

    :param fn: the predicate to test daughters against.

    """
    def _hasDaughter(t):
        if not hasattr(t, '__iter__'):
            return None
        else:
            vals = [fn(d) for d in allDaughters(t)]
            if reduce(functionalOr, vals):
                return t
            else:
                return None
    return SearchFunction(_hasDaughter, fn)

@public
def daughters(fn=identity):
    """Finds and returns all daughters of a node which match a
    predicate.  Only looks at immediate daughters -- see `deep` for
    deep matching.

    :param fn: the predicate to test daughters against.

    """
    def _daughters(t):
        print(t)
        if not hasattr(t, '__iter__'):
            print("ret: " % fn(t))
            return fn(t)
        else:
            vals = [fn(d) for d in allDaughters(t)]
            return [v for v in vals if v]
    return SearchFunction(_daughters, fn)

@public
def firstDaughter(fn=identity):
    """Returns the first (left-to-right) daughter of a node which
    matches a predicate, or nothing if no daughters match.

    :param fn: the predicate to test against.

    """
    def _firstDaughter(t):
        if isinstance(t, str):
            return None
        else:
            for st in t:
                if fn(st):
                    return st
            return None
    return SearchFunction(_firstDaughter, fn)

def hasXSister(fn=identity, sister_fn=allSisters):
    """Internal function.

    TODO: document, don't export
    """
    def _hasXSister(t):
        sisters = sister_fn(t)
        if sisters:
            vals = [fn(s) for s in sisters]
            if reduce(functionalOr, vals):
                return t
            else:
                return None
        else:
            return None
    r = SearchFunction(_hasXSister, fn)
    s = sister_fn_map[sister_fn.__name__]
    r.fn_str = "has" + s[0].upper() + s[1:]
    return r

@public
def hasSister(fn=identity):
    """Tests if a node has a sister matching a predicate, and returns
    the original node if so.

    :param fn: the predicate to test against

    """
    return hasXSister(fn, allSisters)

@public
def hasLeftSister(fn=identity):
    """Like `hasSister`, but only considers sisters to the left of the
    node.

    """
    return hasXSister(fn, allLeftSisters)

@public
def hasRightSister(fn=identity):
    """Like `hasSister`, but only considers sisters to the right of the
    node.

    """
    return hasXSister(fn, allRightSisters)

@public
def hasImmRightSister(fn=identity):
    """Like `hasSister`, but only considers the immediate right sister
    of the original node.

    """
    return hasXSister(fn, nextRightSister)

@public
def hasImmLeftSister(fn=identity):
    """Like `hasSister`, but only considers the immediate left sister
    of the original node.

    """
    return hasXSister(fn, nextLeftSister)

def sistersX(fn=identity, sister_fn=allSisters):
    """Internal function

    TODO: document, don't export

    """
    def _sisters(t):
        vals = [fn(s) for s in sister_fn(t)]
        return [v for v in vals if v]
    r = SearchFunction(_sisters, fn)
    s = sister_fn_map[sister_fn.__name__]
    if not s.startswith("imm"):
        s += "s"
    r.fn_str = s
    return r

@public
def sisters(fn=identity):
    """Tests if a node has any sisters matching a predicate, and returns
    the sister(s) if so.

    :param fn: the predicate to test against

    """
    return sistersX(fn, allSisters)

@public
def leftSisters(fn=identity):
    """Like `sisters`, but only considers sisters to the left of the
    node.

    """
    return sistersX(fn, leftSisters)

@public
def rightSisters(fn=identity):
    """Like `sisters`, but only considers sisters to the right of the
    node.

    """
    return sistersX(fn, rightSisters)

@public
def immLeftSister(fn=identity):
    """Like `sisters`, but only considers the immediate left sister
    of the original node.

    """
    return sistersX(fn, nextLeftSister)

@public
def immRightSister(fn=identity):
    """Like `sisters`, but only considers the immediate right sister
    of the original node.

    """
    return sistersX(fn, nextRightSister)

# TODO: how to handle ignoring parent?
@public
def hasParent(fn=identity):
    """Tests if a node's parent matches a predicate, and returns the
    original node if so.

    :param fn: the predicate to test against

    """
    def _hasParent(t):
        p = t.parent
        if fn(p):
            return t
        else:
            return None
    return SearchFunction(_hasParent, fn)

@public
def parent(fn=identity):
    """Tests if a node's parent matches a predicate, and returns the
    parent node if so.

    :param fn: the predicate to test against

    """
    def _parent(t):
        p = t.parent
        return fn(p)
    return SearchFunction(_parent, fn)

@public
def hasAncestor(fn=identity):
    """Tests if any of a node's ancestors match a predicate, and returns
    the original node if so.

    :param fn: the predicate to test against

    """
    def _hasAncestor(t):
        if t:
            res = hasParent(fn)(t)
            if res or hasAncestor(fn)(t.parent):
                return t
            else:
                return None
        else:
            return None
    return SearchFunction(_hasAncestor, fn)

@public
def ancestor(fn=identity):
    """Tests if any of a node's ancestors match a predicate, and returns
    the first matching ancestor.

    :param fn: the predicate to test against

    """
    def _ancestor(t):
        # All these null checks should be able to be factored out.  but then
        # we have to call through the wrapped fn, not the underscore version
        # as is done here.
        if t:
            p = t.parent
            if fn(p):
                return p
            else:
                return _ancestor(p)
        else:
            return None
    return SearchFunction(_ancestor, fn)

def leftEdge(fn=identity):
    """Internal function.

    TODO: document, don't export

    """
    def _leftEdge(t):
        if fn(t):
            return t
        down_left = t[0]
        while shouldIgnore(down_left) and down_left.right_sibling:
            down_left = down_left.right_sibling
        if isinstance(down_left, T.Tree):
            return leftEdge(fn)(down_left)
        else:
            return None
    return SearchFunction(_leftEdge, fn)

@public
def iPrecedes(fn=identity):
    """Tests if a node immediately precedes (linearly) a node matching a
    predicate, and returns the original node if so.

    :param fn: the predicate to test against

    """
    def _iPrecedes(t):
        this_node = t
        while this_node:
            next_node = this_node.right_sibling
            while next_node and shouldIgnore(next_node):
                next_node = next_node.right_sibling
            if next_node:
                if leftEdge(fn)(next_node):
                    return t
            this_node = this_node.parent
        return None
    return SearchFunction(_iPrecedes, fn)

# TODO: don't count traces etc as leaves?  and word-level conjunction
@public
def isLeaf():
    """Tests if a node is a leaf node."""
    def _isLeaf(t):
        if util.isLeafNode(t):
            return t
        else:
            return None
    return SearchFunction(_isLeaf)

@public
def isRoot():
    """Tests if this node is the root of its tree.  The root is the top
    of the actual sentence, not the higher node dominating the sentence
    as well as associated metadata.

    """
    def _isRoot(t):
        if t.parent.node == "":
            return t
        else:
            return None
    return SearchFunction(_isRoot)

@public
def daughterCount(n, match="equal"):
    """Tests if the target node has a certain number of daughters.

    :param n: the desired number of daughters

    :param match: controls the behavior of the matching.  One of
        \"equal\", \"less\", or \"greater\".

    """
    if match != "equal" and match != "less" and match != "greater":
        raise Exception("match argument to daughterCount is misspecified")

    def _daughterCount(t):
        have_match = False
        if match == "equal":
            if len(t) == n:
                have_match = True
        elif match == "less":
            if len(t) < n:
                have_match = True
        elif match == "greater":
            if len(t) > n:
                have_match = True
        if have_match:
            return t
        else:
            return None
    return SearchFunction(_daughterCount, "%s, match='%s'" % (n, match))

@public
def coIndexed(fn=identity):
    """Tests if any nodes coindexed with the original node match a
    predicate.  Returns the matching coindexed nodes.

    :param fn: the predicate to test against

    """
    def _coIndexed(t):
        the_idx = util.index(t)
        if the_idx == 0:
            return None
        c = t.root.subtrees(lambda x: util.index(x) == the_idx and
                            x != t)
        c = list(c)
        c = filter(fn, c)
        return c
    return SearchFunction(_coIndexed, fn)

@public
def hasCoIndexed(fn=identity):
    """Tests if any nodes coindexed with the original node match a
    predicate.  Returns the original node.

    :param fn: the predicate to test against

    """
    def _hasCoIndexed(t):
        the_idx = util.index(t)
        if the_idx == 0:
            return None
        c = t.root.subtrees(lambda x: util.index(x) == the_idx and
                            x != t)
        c = list(c)
        c = filter(fn, c)
        if c and len(c) > 0:
            return t
        else:
            return None
    return SearchFunction(_hasCoIndexed, fn)

@public
def antecedent(fn=identity):
    """Tests whether the antecedent of a node matches a predicate, and
    returns the antecedent if so.  The antecedent of a node is the
    unique node which is coindexed with that node, and is not itself a
    trace.  If the original node is not a trace, no match is returned.

    :param fn: the predicate to test against

    """
    # TODO: test whether the target node is a trace
    def _antecedent(t):
        the_idx = util.index(t)
        if the_idx == 0:
            return None
        c = t.root.subtrees(lambda x: util.index(x) == the_idx and
                            isinstance(x[0], T.Tree))
        c = list(c)
        if len(c) == 1:
            if fn(c[0]):
                return c[0]
            else:
                return None
        else:
            return None
    return SearchFunction(_antecedent, fn)

@public
def hasAntecedent(fn=identity):
    """Tests whether the antecedent of a node matches a predicate, and
    returns the original node if so.  The antecedent of a node is the
    unique node which is coindexed with that node, and is not itself a
    trace.  If the original node is not a trace, no match is returned.

    :param fn: the predicate to test against

    """
    def _hasAntecedent(t):
        the_idx = util.index(t)
        if the_idx == 0:
            return None
        c = t.root.subtrees(lambda x: util.index(x) == the_idx and
                            isinstance(x[0], T.Tree))
        # Need to convert generator -> list to check length
        c = list(c)
        if len(c) == 1:
            if fn(c[0]):
                return t
            else:
                return None
        else:
            return None
    return SearchFunction(_hasAntecedent, fn)

@public
def isTrace():
    """Tests whether a node is a trace."""
    def _isTrace(t):
        if util.isTrace(t):
            return t
        else:
            return None
    return SearchFunction(_isTrace, "")

@public
def isGapped():
    """Tests whether a node is the reduced half of a gapping construction.

    Such nodes can be expected to be structurally deficient in ways not
    allowed of ordinary nodes.

    """
    def _isGapped(t):
        if "=" in t.node:
            return t
        else:
            return None
    return SearchFunction(_isGapped, "")

@public
def isIndexed():
    """Tests whether a node has a numerical index, of any variety."""
    def _isIndexed(t):
        if util.isTrace(t):
            try:
                int(t[0].split("-")[-1])
                return t
            except ValueError:
                return None
        else:
            if isGapped(t):
                return t
            else:
                try:
                    int(t.node.split("-")[-1])
                    return t
                except ValueError:
                    return None
    return SearchFunction(_isIndexed, "")

@public
def sharesLabelWith(fn=identity, all=False):
    """Test whether a node shares a label with another.

    The supplied search function picks out the set of nodes, beginning
    with the current node, to test for same-label-ness.

    :param fn: which nodes to test

    :param all: whether all nodes picked out by ``fn`` should match, or
        (the default) just one

    """
    def _sharesLabelWith(t):
        the_label = t.node
        candidates = fn(t)
        # TODO: If we mandated that searchfns return lists, then there
        # would be no need to do this...
        for c in util.iter_flatten([candidates]):
            if c.node == the_label:
                if not all:
                    return t
            else:
                if all:
                    return None
        if all:
            return t
        else:
            return None
    return SearchFunction(_sharesLabelWith, "%s, all='%s'" % (fn, all))

@public
def sharesLabelWithMod(fn=identity, all=False, comparator=operator.eq):
    """Test whether a node shares a label with another.

    The supplied search function picks out the set of nodes, beginning
    with the current node, to test for same-label-ness.

    :param fn: which nodes to test

    :param all: whether all nodes picked out by ``fn`` should match, or
        (the default) just one

    :param transformer: a two-argument function, called with the label
        of the anchor node and (sequentially) each target matching
        ``fn``.  Should return ``True`` if the labels match, and
        ``False`` otherwise.

    """
    def _sharesLabelWithMod(t):
        the_label = t.node
        candidates = fn(t)
        if not candidates:
            return None
        # TODO: If we mandated that searchfns return lists, then there
        # would be no need to do this...
        for c in util.iter_flatten([candidates]):
            if comparator(the_label, c.node):
                if not all:
                    return t
            else:
                if all:
                    return None
        if all:
            return t
        else:
            return None
    return SearchFunction(_sharesLabelWithMod,
                          '%s, all="%s", comparator="%s"' %
                          (fn, all, comparator))


# Function modifiers

def reduceHack(x, y):
    # This implementation is too fault-tolerant to inspire confidence.
    # I'd rather it break if there's a bug.
    # if not isinstance(x, list):
    #     x = [x]
    # if hasattr(y, "__iter__"):
    #     x.extend(y)
    # else:
    #     x.append(y)
    # return x

    x.extend(y)
    return x

@public
def deep(fn):
    """Recursively applies a predicate to the target node and all
    descendants at any depth, returning any and all matching
    descendants.

    TODO: usage examples

    :param fn: the predicate to deepen

    """
    def _deep(t):
        # TODO: We have null handling here is because we don't go
        # through SearchFunction again.  Should we?
        if t:
            ret = t.subtrees
            ret = map(fn, ret)
            # TODO: we don't want this forcing, but without it, we get buried
            # too deep in lists
            return list(x for x in util.iter_flatten(ret) if x)
        else:
            return t
    return SearchFunction(_deep, fn)

@public
def ignoring(ignore_fn, fn):
    """Ignore nodes functionality, currently inoperative."""
    def _ignoring(t):
        old_ignore = setIgnore(ignore_fn)
        res = fn(t)
        setIgnore(old_ignore)
        return res
    return SearchFunction(_ignoring, 'ignore_fn="%s", fn="%s"' %
                          (ignore_fn, fn))

# Utility functions

# TODO: don't export these below

# Boolean operations as language keywords is dumb
def functionalSSOr(x, y):
    if x:
        return x
    else:
        return y

def functionalOr(x, y):
    return x or y
