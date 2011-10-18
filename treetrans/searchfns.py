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
        if not shouldIgnore(t):
            res.append(t)
    return res

def allRightSisters(t):
    res = []
    while t:
        t = t.right_sibling
        if not shouldIgnore(t):
            res.append(t.right_sibling)
    return res

def allSisters(t):
    return allLeftSisters(t).extend(allRightSisters(t))

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
                if exact_match or to_match[slice(len(label)+1)] == label + "-":
                    return t
                else:
                    return None
    return SearchFunction(_hasLabel)

# TODO: handle ignore
def hasLeafLabel(label):
    def _hasLeafLabel(t):
        if len(t) == 1 and isinstance(t[0], str):
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
                    return None
        else:
            return None
    return SearchFunction(_hasLeafLabel)

default_ignore_function = hasLabel("CODE") | hasLabel("ID") # ...

def hasLemma(lemma):
    if hasattr(lemma, "pattern"):
        lemma = lemma.pattern
    return hasLeafLabel(re.compile("^.*-(" + lemma + ")$"))
def hasWord(word):
    if hasattr(word, "pattern"):
        word = word.pattern
    return hasLeafLabel(re.compile("^(" + word + ")-"))

def hasDaughter(fn = identity):
    def _hasDaughter(t):
        if isinstance(t, str):
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
        if isinstance(t, str):
            return None
        else:
            vals = [fn(d) for d in allDaughters(t)]
            return [v for v in vals if v]
    return SearchFunction(_daughters)

def hasXSister(fn = identity, sisterFn = allSisters):
    def _hasXSister(t):
        vals = [fn(s) for s in sisterFn(t)]
        if reduce(functionalOr, vals):
            return t
        else:
            return None
    return SearchFunction(_hasXSister)

def hasSister(fn = identity):
    return hasXSister(fn, allSisters)
def hasLeftSister(fn = identity):
    return hasXsister(fn, allLeftSisters)
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
        return fn(p)
    return SearchFunction(_hasParent)

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
