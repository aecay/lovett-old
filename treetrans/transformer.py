import nltk.tree as T
import re

class TreeTransformer:
    def __init__(self, tree):
        # Do not mutate the tree we are given -- make a copy for our use.
        self._tree = tree.copy(True)
        self._matches = []

    # remove me?
    def _testPos(self, p, fn):
        # temp = TreeTransformer(self._tree, [p])
        return fn(self._tree[p])

    def findNodes(self, fn = lambda x: True):
        self._matches = []
        for p in self._tree.treepositions():
            res = fn(self._tree[p])
            if res:
                if isinstance(res, list) and not isinstance(res, T.Tree):
                    self._matches.extend(res)
                else:
                    self._matches.append(res)
        return self

    # Should we remove this?  It is probably never necessary, except for
    # convenience, and it makes things complicated (can filter turn a
    # single match into a list?)
    def filterMatches(self, fn = lambda x: True):
        vals = [fn(p) for p in self._matches]
        self._matches = [self._matches[i] for i in range(len(self._matches)) \
                             if vals[i]]
        return self

    # TODO: make sure that the modification functions are updateing
    # matches in a coherent way.  Ex. prune should empty matches.

    def addParentNode(self, name):
        for m in self._matches:
            barf = T.ParentedTree("BARF", [])
            t = self._tree
            pos = m.treepos
            temp = t[pos]
            t[pos] = barf
            t[pos] = T.ParentedTree(name, [temp])
        return self

    # TODO: option to move left instead of right
    def addParentNodeSpanning(self, name, fn, immediate = False):
        # Must be done in two steps because otherwise we shit all over
        # our list of positions.  ...then we switched to storing matches
        # as trees, not positions, but why mess with what works?

        # TODO: actually, we have to do each transformation as we find
        # it.  Otherwise, we will do weird things if we have ex. N N ADJ
        # and we try to extend NP over N...ADJ.

        # list of tuples of (beginning node, node list)
        to_perform = []
        for m in self._matches:
            done = False
            failed = False
            acc = []
            p = m
            while not done:
                print p
                p = p.right_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        done = True
                        to_perform.append((m, acc))
                    if immediate:
                        done = True
                else:
                    done = True
            
        for (node, lst) in to_perform:
            barf = T.ParentedTree("BARF", [])
            t = self._tree
            for n in lst:
                del t[n.treepos]
            p = node.treepos
            t[p] = barf
            t[p] = T.ParentedTree(name, [node] + lst)
        return self

    # TODO: move left instead of right
    def extendUntil(self, fn, immediate = False):
        to_perform = []
        for m in self._matches:
            p = m
            acc = []
            done = False
            while not done:
                p = p.right_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        for a in acc:
                            del self._tree[a.treepos]
                            m.append(a)
                        done = True
                    if immediate:
                        done = True
                else:
                    done = True
        return self

    def changeLabel(self, label = "", fn = None):
        # TODO: Raise an error if neither label or fn given
        if fn:
            for m in self._matches:
                m.node = fn(m.node)
        else:
            for m in self._matches:
                m.node = label
        return self

    def addSister(self, label = "XXX", word = "X-X", tree = None, before = True):
        for m in self._matches:
            p = m.parent
            pi = m.parent_index
            to_insert = tree or T.ParentedTree(label, [word])
            if not before:
                pi = pi + 1
            p.insert(pi, to_insert)
        return self

    def prune(self):
        for m in self._matches:
            p = m.parent
            pi = m.parent_index + 1
            for d in m:
                del self._tree[d.treepos]
                p.insert(pi, d)
            del self._tree[m.treepos]

    def matches(self):
        return self._matches

    def matchpos(self):
        return map(lambda x: x.treepos, self._matches)

    def tree(self):
        return self._tree

    def pt(self):
        return self._tree.pprint()


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
    return hasLeafLabel(re.compile("^.*-" + lemma + "$"))
def hasWord(word):
    return hasLeafLabel(re.compile("^" + word + "-"))

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
    def _hasSister(t):
        vals = [fn(s) for s in sisterFn(t)]
        if reduce(functionalOr, vals):
            return t
        else:
            return None
    return SearchFunction(_hasSister)

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

t = T.ParentedTree("( (IP (Q very) (, ,) (ADV slowly) (N foo) (V bar) (D baz) (ADJ spam) (N quux) (D irrelevant)))")

tt = TreeTransformer(t)

def test():
    tmp = TreeTransformer(t)
    tmp.findNodes(hasLabel("N"))
    print "haslabel N"
    print tmp.matches()
    tmp.findNodes(hasLabel("V")).addParentNode("VP")
    print "v addparent vp"
    print tmp.pt()
    tmp.findNodes(hasLabel("D")).addParentNodeSpanning("NP", hasLabel("N"))
    print "d..n addparent spanning np"
    print tmp.pt()
    tmp.findNodes(hasLabel("V")).addSister("CL", "lo-el")
    print "v addsister cl"
    print tmp.pt()
    tmp.findNodes(hasLabel("Q")).addParentNode("QP")
    tmp.findNodes(hasLabel("QP")).extendUntil(hasLabel("ADV"))
    print "qp extenduntil adv"
    print tmp.pt()
    tmp.findNodes(hasLabel("IP") & hasDaughter(hasLabel("NP")))
    print "ip hasdaughter vp"
    print tmp.matches()
    tmp.findNodes(hasLabel("IP") & daughters(hasLabel("VP")))
    print "ip daughters vp"
    print tmp.matches()
    tmp.findNodes(hasLabel("IP") & deep(hasLabel("N")))
    print "ip deep haslabel n"
    print tmp.matches()
    tmp.findNodes(hasLabel("V") & iPrecedes(hasLabel("D")))
    print "v iprecedes d"
    print tmp.matches()
    tmp.findNodes(hasLabel("N")).addParentNode("M")
    tmp.findNodes(hasLabel("IP") & deep(hasLabel("N")))
    print "ip deep haslabel n"
    print tmp.matches()
    tmp.findNodes(hasLabel("IP") & daughters(~hasLabel("NP")))
    print "ip daughters not haslabel np"
    print tmp.matches()
    tmp.findNodes(hasLabel("Q") & iPrecedes(hasLabel("ADV")))
    print "q iprecedes adv"
    print tmp.matches()
    tmp.findNodes(ignoring(hasLabel(","), hasLabel("Q") & iPrecedes(hasLabel("ADV"))))
    print "q iprecedes adv ignoring ,"
    print tmp.matches()
    tmp.findNodes(hasLabel("QP") & daughters())
    print "qp daughters"
    print tmp.matches()
    tmp.findNodes(hasLabel("QP") & ignoring(hasLabel(","), daughters()))
    print "qp daughters ignoring ,"
    print tmp.matches()
    tmp.findNodes(hasLabel(",") & hasAncestor(hasLabel("IP")))
    print ", hasancestor ip"
    print tmp.matches()
    tmp.findNodes(hasLemma("el"))
    print "haslemma el"
    print tmp.matches()
    tmp.findNodes(hasLabel("M")).prune()
    print "prune m"
    print tmp.pt()
    
