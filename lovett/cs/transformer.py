import copy

import lovett.tree
import lovett.util

import itertools

# TODO: addDashTag
# TODO: look at conversations w jana for good ideas

class TreeTransformer:
    def __init__(self, sentence):
        self._sentence = sentence
        self._tree = sentence.tree()
        self._matches = []
        self._max_trace = lovett.util.largest_index(self._tree)
        self._made_copy = False

    def _mutate(self):
        pass
    # TODO: worry about this
        # if not self._made_copy:
        #     self._tree = copy.deepcopy(self.tree())
        #     self._made_copy = True

    # remove me?
    def _testPos(self, p, fn):
        # temp = TreeTransformer(self._tree, [p])
        return fn(self._tree[p])

    # TODO: add shortcut to call with just a string -> hasLabel

    # TODO: add depth argument to allow restricting the depth of
    # searches and/or add "findFromRoot" which only calls the predicate
    # with the root node
    def findNodes(self, fn=lambda x: x, deep=True):
        self._matches = []
        if deep:
            # TODO: kludge!
            to_match = itertools.chain([self._tree], self._tree.subtrees())
        else:
            to_match = self._tree
        for p in to_match:
            res = fn(p)
            if res is not None:
                # Fuck, this is excruciating
                self._matches.extend(list(lovett.util.iter_flatten([res])))
        return self

    # TODO: consolidate these
    def storeMatchData(self, fn):
        self._matchData = map(fn, self._matches)

    def queryMatches(self, fn):
        return map(fn, self._matches)

    # Should we remove this?  It is probably never necessary, except for
    # convenience, and it makes things complicated (can filter turn a
    # single match into a list?)  Update: Don't remove -- in tree
    # building, it is useful to move pointer -- but perhaps give a
    # better name
    def filterMatches(self, fn=lambda x: x):
        new_matches = []
        new_match_data = []
        for m in range(len(self._matches)):
            res = fn(self._matches[m])
            if res:
                # TODO: make eatch match be an object, with metadata
                # dict.  then map \x -> ObjWMD(x, old_md) over the list
                # of results here
                new_matches += list(lovett.util.iter_flatten([res]))
                new_match_data += [self._matchData[m]] * len(res)
        self._matches = new_matches
        self._matchData = new_match_data
        return self

    # TODO: make sure that the modification functions are updateing
    # matches in a coherent way.  Ex. prune should empty matches.

    def addParentNode(self, name, move_index=False):
        self._mutate()
        for m in self._matches:
            barf = lovett.tree.ParentedTree("BARF", [])
            t = self._tree
            pos = m.treepos
            old = t[pos]
            t[pos] = barf
            new = lovett.tree.ParentedTree(name, [old])
            if move_index:
                index = lovett.util.remove_index(old)
                lovett.util.set_index(new, index)
            t[pos] = new
        return self

    def addParentNodeSpanning(self, name, fn, immediate=False, right=True,
                              to_end=False):
        """Add a node over the matched node and some of its siblings.

        :param name: the name of the node to add
        :type name: string
        :param fn: a predicate indicating where to stop adding siblings to the new parent
        :type fn: function
        :param immediate: whether the predicate ``fn`` must match the immediate sibling
        :type immediate: boolean
        :param right: whether to look to the right or to the left for siblings
        :type right: boolean
        :param to_end: unimplemented TODO
        :type to_end: boolean"""

        # TODO: simplify this by using a dual match, then making addParent
        # polymorphic?

        # Must be done in two steps because otherwise we shit all over
        # our list of positions.  ...then we switched to storing matches
        # as trees, not positions, but why mess with what works?

        # DONE: actually, we have to do each transformation as we find
        # it.  Otherwise, we will do weird things if we have ex. N N ADJ
        # and we try to extend NP over N...ADJ.

        self._mutate()

        barf = lovett.tree.ParentedTree("BARF", [])
        t = self._tree
        for m in self._matches:
            p = m
            acc = [p]
            while True:
                if right:
                    p = p.right_sibling
                else:
                    p = p.left_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        if not right:
                            acc.reverse()
                        for n in acc:
                            del t[n.treeposition]
                        pp = m.treepossition
                        t[pp] = barf
                        t[pp] = lovett.tree.ParentedTree(name, acc)
                        break
                    if immediate:
                        break
                else:
                    break
        return self

    # Instead of immediate -- another function extendOne?
    # also need more general movt fns.
    def extendUntil(self, fn, immediate=False, right=True):
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
                                m.insert(0, a)
                        done = True
                    if immediate:
                        done = True
                else:
                    done = True
        return self

    def changeLabel(self, label="XXX"):
        self._mutate()
        if hasattr(label, "__call__"):
            for m in self._matches:
                m.label = label(m.label)
        else:
            for m in self._matches:
                m.label = label
        return self

    def addSister(self, label="XXX", word="X-X", tree=None, before=True,
                  coindex=False):
        self._mutate()
        for m in self._matches:
            p = m.parent
            pi = m.parent_index
            to_insert = tree or lovett.tree.ParentedTree(label, [word])
            if coindex:
                index = self._max_trace + 1
                # TODO(?): a way to add gapping indices with = instead of -
                lovett.util.set_index(m, index)
                lovett.util.set_index(to_insert, index)
                self._max_trace = index
            if not before:
                pi = pi + 1
            p.insert(pi, to_insert)
        return self

    def addDaughter(self, label="XXX", word="X-X", tree=None):
        self._mutate()
        for m in self._matches:
            to_insert = tree or lovett.tree.ParentedTree(label, [word])
            m.insert(0, to_insert)
        return self

# TODO: add a coindex function, operating on a dual selection

    def prune(self):
        self._mutate()
        for m in self._matches:
            p = m.parent
            pi = m.parent_index + 1
            for d in m:
                del self._tree[d.treepos]
                p.insert(pi, d)
            del self._tree[m.treepos]

    def withMatchAndData(self, fn):
        # TODO: convert all other convenience fns to special cases of this one
        # TODO: extend notion of match to allow multiples
        for i in range(len(self._matches)):
            self._matches[i] = fn(self._matches[i], self._matchData[i])

    # TODO: raiseNode

    # TODO: @property
    def matches(self):
        return self._matches

    def matchpos(self):
        return map(lambda x: x.treepos, self._matches)

    def tree(self):
        return self._tree

    def pt(self):
        # TODO: remove, replace with __unicode__
        return str(self._tree)

    def __str__(self):
        return str(self._tree)


# TODO: what happens if we do ~daughters(...) ? Should not be
# defined/create an error?
