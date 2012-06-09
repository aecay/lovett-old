import nltk.tree as T
import util

# TODO: addDashTag
# TODO: look at conversations w jana for good ideas

class TreeTransformer:
    def __init__(self, tree):
        # Do not mutate the tree we are given -- make a copy for our use.
        self._tree = tree.copy(True)
        self._matches = []
        self._max_trace = util.getLargestIndex(self._tree)

    # remove me?
    def _testPos(self, p, fn):
        # temp = TreeTransformer(self._tree, [p])
        return fn(self._tree[p])

    # TODO: add shortcut to call with just a string -> hasLabel
    def findNodes(self, fn = lambda x: x):
        self._matches = []
        for p in self._tree.subtrees():
            res = fn(p)
            if res:
                # Fuck, this is excruciating
                self._matches.extend(list(util.iter_flatten([res])))
        return self

    # Should we remove this?  It is probably never necessary, except for
    # convenience, and it makes things complicated (can filter turn a
    # single match into a list?)  Update: Don't remove -- in tree
    # building, it is useful to move pointer -- but perhaps give a
    # better name
    def filterMatches(self, fn = lambda x: x):
        new_matches = []
        for m in self._matches:
            res = fn(m)
            if res:
                new_matches = list(util.iter_flatten([res]))
        self._matches = new_matches
        return self

    # TODO: make sure that the modification functions are updateing
    # matches in a coherent way.  Ex. prune should empty matches.

    def addParentNode(self, name, moveIndex = False):
        for m in self._matches:
            barf = T.ParentedTree("BARF", [])
            t = self._tree
            pos = m.treepos
            old = t[pos]
            t[pos] = barf
            new = T.ParentedTree(name, [old])
            if moveIndex:
                index = util.removeIndexFromTree(old)
                util.addIndexToTree(index, new)
            t[pos] = new
        return self

    def addParentNodeSpanning(self, name, fn, immediate = False, right = True,
                              to_end = False):
        # Must be done in two steps because otherwise we shit all over
        # our list of positions.  ...then we switched to storing matches
        # as trees, not positions, but why mess with what works?

        # DONE: actually, we have to do each transformation as we find
        # it.  Otherwise, we will do weird things if we have ex. N N ADJ
        # and we try to extend NP over N...ADJ.

        barf = T.ParentedTree("BARF", [])
        t = self._tree
        for m in self._matches:
            acc = []
            p = m
            while True:
                if right:
                    p = p.right_sibling
                else:
                    p = p.left_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        if not right:
                            # I'm not sure if this is strictly necessary
                            acc.reverse()
                        for n in acc:
                            del t[n.treepos]
                        pp = m.treepos
                        t[pp] = barf
                        t[pp] = T.ParentedTree(name, [m] + acc)
                        break
                    if immediate:
                        break
                else:
                    break
            
        return self

    # Instead of immediate -- another function extendOne?
    # also need more general movt fns.
    def extendUntil(self, fn, immediate = False, right = True):
        for m in self._matches:
            p = m
            acc = []
            done = False
            while not done:
                if right:
                    p = p.right_sibling
                else:
                    p = p.left_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        for a in acc:
                            del self._tree[a.treepos]
                            if right:
                                m.append(a)
                            else:
                                m.insert(0,a)
                        done = True
                    if immediate:
                        done = True
                else:
                    done = True
        return self

    def changeLabel(self, label = "XXX"):
        if hasattr(label, "__call__"):
            for m in self._matches:
                m.node = label(m.node)
        else:
            for m in self._matches:
                m.node = label
        return self

    def addSister(self, label = "XXX", word = "X-X", tree = None, before = True,
                  coindex = False):
        for m in self._matches:
            p = m.parent
            pi = m.parent_index
            to_insert = tree or T.ParentedTree(label, [word])
            if coindex:
                index = self._max_trace + 1
                # TODO(?): a way to add gapping indices with = instead of -
                util.addIndexToTree(index, m)
                util.addIndexToTree(index, to_insert)
                self._max_trace = index
            if not before:
                pi = pi + 1
            p.insert(pi, to_insert)
        return self

    def addDaughter(self, label = "XXX", word = "X-X", tree = None):
        for m in self._matches:
            to_insert = tree or T.ParentedTree(label, [word])
            m.insert(0, to_insert)
        return self

# TODO: add a coindex function, operating on a dual selection

    def prune(self):
        for m in self._matches:
            p = m.parent
            pi = m.parent_index + 1
            for d in m:
                del self._tree[d.treepos]
                p.insert(pi, d)
            del self._tree[m.treepos]

    # TODO: raiseNode

    # TODO: @property
    def matches(self):
        return self._matches

    def matchpos(self):
        return map(lambda x: x.treepos, self._matches)

    def tree(self):
        return self._tree

    def pt(self):
        return self._tree.pprint()


# TODO: what happens if we do ~daughters(...) ? Should not be
# defined/create an error?
