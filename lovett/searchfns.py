import nltk.tree as T
import re

# Match functions

class SearchFunction:
    def __init__(self, fn):
        self.fn = fn

    # is this the place to put the ignore logic?
    def __call__(self, arg):
        # This if statement is so that non-results percolate through a chained function.
        if arg:
            # Handle lists, returned by sister() etc.  this is looking
            # ugly, as we also handle lists in the treetransformer class
            if isinstance(arg, list) and not isinstance(arg, T.Tree):
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
        return SearchFunction(_and)

    def __or__(self, other):
        def _or(t):
            res = self(t)
            if res:
                return res
            else:
                return other(t)
        return SearchFunction(_or)

    def __invert__(self):
        def _close(fn):
            def _not(t):
                if fn(t):
                    return None
                else:
                    return t
            return _not
        self.fn = _close(self.fn)
        return self


# TODO: add below methods to (subclass of) ParentedTree?

# Ignoring things
ignore_function = SearchFunction(lambda x: False)
# Because of mutual recursion with this and hasLabel, the actual value
# is filled in below
default_ignore_function = lambda x: False

def setIgnore(fn):
    global ignore_function
    old_ignore = ignore_function
    ignore_function = fn
    return old_ignore

def shouldIgnore(t):
    return ignore_function(t) or default_ignore_function(t)

# Access functions
    
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
    s = allLeftSisters(t).extend(allRightSisters(t))
    return s

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
    return [d for d in t if not shouldIgnore(d)]

# Utility functions

# Something which is dumb: not having an identity function in your
# standard library.
def identity(x):
    return x

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
def hasLabel(label, exact = False):
    def _hasLabel(t):
        to_match = ""
        if isinstance(t, T.Tree):
            to_match = t.node
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
                if exact_match or to_match[slice(len(label)+1)] == label + "-":
                    return t
                else:
                    return None
    return SearchFunction(_hasLabel)

# TODO: handle ignore
def hasLeafLabel(label):
    def _hasLeafLabel(t):
        if len(t) == 1 and isinstance(t[0], basestring):
            if hasattr(label, "match"):
                if label.match(t[0]):
                    return t
                else:
                    return None
            else:
                exact_match = label == t[0]
                if exact_match:
                    return t
                else:
                    if t[0][slice(len(label) + 1)] == label + "-":
                        return t
                    else:
                        return None
        else:
            return None
    return SearchFunction(_hasLeafLabel)

default_ignore_function = hasLabel("CODE") | hasLabel("ID") # ...

def hasLemma(lemma):
    if hasattr(lemma, "pattern"):
        lemma = lemma.pattern
    else:
        lemma = re.escape(lemma)
    return hasLeafLabel(re.compile("^.*-(" + lemma + ")$"))

def hasWord(word):
    if hasattr(word, "pattern"):
        word = word.pattern
    else:
        word = re.escape(word)
    return hasLeafLabel(re.compile("^(" + word + ")-"))

def hasDashTag(tag):
    return hasLabel(re.compile(".*-" + tag + "(-|$)"))

def hasDaughter(fn = identity):
    def _hasDaughter(t):
        if isinstance(t, basestring):
            return None
        else:
            vals = [fn(d) for d in allDaughters(t)]
            if reduce(functionalOr, vals):
                return t
            else:
                return None
    return SearchFunction(_hasDaughter)

def daughters(fn = identity):
    def _daughters(t):
        if isinstance(t, basestring):
            return None
        else:
            vals = [fn(d) for d in allDaughters(t)]
            return [v for v in vals if v]
    return SearchFunction(_daughters)

def firstDaughter(fn = identity):
    def _firstDaughter(t):
        if isinstance(t, basestring):
            return None
        else:
            for st in t:
                if fn(st):
                    return st
            return None
    return SearchFunction(_firstDaughter)

def hasXSister(fn = identity, sisterFn = allSisters):
    def _hasXSister(t):
        sisters = sisterFn(t)
        if sisters:
            vals = [fn(s) for s in sisters]
            if reduce(functionalOr, vals):
                return t
            else:
                return None
        else:
           return None     
    return SearchFunction(_hasXSister)

def hasSister(fn = identity):
    return hasXSister(fn, allSisters)
def hasLeftSister(fn = identity):
    return hasXSister(fn, allLeftSisters)
def hasRightSister(fn = identity):
    return hasXSister(fn, allRightSisters)
def hasImmRightSister(fn = identity):
    return hasXSister(fn, nextRightSister)
def hasImmLeftSister(fn = identity):
    return hasXSister(fn, nextLeftSister)

def sistersX(fn = identity, sisterFn = allSisters):
    def _sisters(t):
        vals = [fn(s) for s in sisterFn(t)]
        return [v for v in vals if v]
    return SearchFunction(_sisters)

def sisters(fn = identity):
    return sistersX(fn, allSisters)
def leftSisters(fn = identity):
    return sistersX(fn, leftSisters)
def rightSisters(fn = identity):
    return sistersX(fn, rightSisters)
def immLeftSister(fn = identity):
    return sistersX(fn, nextLeftSister)
def immRightSister(fn = identity):
    return sistersX(fn, nextRightSister)

# TODO: how to handle ignoring parent?
def hasParent(fn = identity):
    def _hasParent(t):
        p = t.parent
        if fn(p):
            return t
        else:
            return None
    return SearchFunction(_hasParent)

def parent(fn = identity):
    def _parent(t):
        p = t.parent
        return fn(p)
    return SearchFunction(_parent)

def hasAncestor(fn = identity):
    def _hasAncestor(t):
        if t:
            res = hasParent(fn)(t)
            if res or hasAncestor(fn)(t.parent):
                return t
            else:
                return None
        else:
            return None
    return SearchFunction(_hasAncestor)

def ancestor(fn = identity):
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
    return SearchFunction(_ancestor)

def leftEdge(fn = identity):
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
    return SearchFunction(_leftEdge)

def iPrecedes(fn = lambda x: x):
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
    return SearchFunction(_iPrecedes)

def isLeaf():
    def _isLeaf(t):
        if not isinstance(t[0], T.Tree):
            return t
        else:
            return None
    return SearchFunction(_isLeaf)

# Function modifiers

def reduceHack(x,y):
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

def deep(fn):
    def _deep(t):
        # TODO: We have null handling here is because we don't go
        # through SearchFunction again.  Should we?
        if t:
            # The code elves gave me this.  Deep returns a list.
            # Daughters also returns a list, so we get nested lists.
            # The reduce un-nests them.
            ds = daughters(deep(fn))(t)
            if ds: 
                ds = reduce(reduceHack, [l for l in daughters(deep(fn))(t) \
                                             if hasattr(l, "__iter__")])
            res = [fn(t)]
            if isinstance(ds, list):
                res.extend(ds)
            ret = [r for r in res if r]
            return ret
        else:
            return t
    return SearchFunction(_deep)

def ignoring(ignore_fn, fn):
    def _ignoring(t):
        old_ignore = setIgnore(ignore_fn)
        res = fn(t)
        setIgnore(old_ignore)
        return res
    return SearchFunction(_ignoring)

# Utility functions

# Boolean operations as language keywords is dumb
def functionalSSOr(x, y):
    if x:
        return x
    else:
        return y

def functionalOr(x,y):
    return x or y
