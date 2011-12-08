import nltk.tree as T

def parseTraces(tree):
    # TODO: this must be made to understand the new format, where I
    # think I want indices in METADATA
    def getTrace(tree):
        temp = tree.node.split("-")
        temp.pop()          # remove the lemma
        temp2 = 0
        try:
            temp2 = int(temp[-1])
        except ValueError:
            # last element is not a parseable number
            pass
        except IndexError:
            # the list had only 1 item, and is now empty
            pass
        return temp2
    return reduce(max, map(getTrace, tree.subtrees()))

def addIndexToTree(index, tree):
    # TODO: do dash-tags go inside or outside index?
    if isinstance(tree[0], str) and tree[0][0] == "*":
        # This is an EC; so add index to the leaf
        temp = tree[0].split("-")
        if len(temp) == 1:
            temp.append(str(index))
        else:
            temp.insert(-1, str(index))
        tree[0] = "-".join(temp)
    else:
        # not EC; add index to the label
        tree.node = tree.node + "-" + str(index)

class TreeTransformer:
    def __init__(self, tree):
        # Do not mutate the tree we are given -- make a copy for our use.
        self._tree = tree.copy(True)
        self._matches = []
        self._max_trace = parseTraces(self._tree)

    # remove me?
    def _testPos(self, p, fn):
        # temp = TreeTransformer(self._tree, [p])
        return fn(self._tree[p])

    # TODO: add shortcut to call with just a string -> hasLabel
    def findNodes(self, fn = lambda x: x):
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
    # single match into a list?)  Update: Don't remove -- in tree
    # building, it is useful to move pointer -- but perhaps give a
    # better name
    def filterMatches(self, fn = lambda x: x):
        new_matches = []
        for m in self._matches:
            res = fn(m)
            if res:
                if isinstance(res, list) and not isinstance(res, T.Tree):
                    new_matches.extend(res)
                else:
                    new_matches.append(res)
        self._matches = new_matches
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

    def addParentNodeSpanning(self, name, fn, immediate = False, right = True):
        # Must be done in two steps because otherwise we shit all over
        # our list of positions.  ...then we switched to storing matches
        # as trees, not positions, but why mess with what works?

        # DONE: actually, we have to do each transformation as we find
        # it.  Otherwise, we will do weird things if we have ex. N N ADJ
        # and we try to extend NP over N...ADJ.

        barf = T.ParentedTree("BARF", [])
        t = self._tree
        for m in self._matches:
            done = False
            acc = []
            p = m
            while not done:
                if right:
                    p = p.right_sibling
                else:
                    p = p.left_sibling
                if p:
                    acc.append(p)
                    if fn(p):
                        done = True
                        if not right:
                            # I'm not sure if this is strictly necessary
                            acc.reverse()
                        for n in acc:
                            del t[n.treepos]
                        pp = m.treepos
                        t[pp] = barf
                        t[pp] = T.ParentedTree(name, [m] + acc)
                    if immediate:
                        done = True
                else:
                    done = True
            
        return self

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
                addIndexToTree(index, m)
                addIndexToTree(index, to_insert)
                self._max_trace = index
            if not before:
                pi = pi + 1
            p.insert(pi, to_insert)
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

    def matches(self):
        return self._matches

    def matchpos(self):
        return map(lambda x: x.treepos, self._matches)

    def tree(self):
        return self._tree

    def pt(self):
        return self._tree.pprint()



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
    tmp.findNodes(hasLabel("N") & hasParent(hasLabel("NP")))
    print "n hasparent np"
    print tmp.matches()
    tmp.findNodes(hasLabel("M")).prune()
    print "prune m"
    print tmp.pt()
    tmp.findNodes(hasLabel("NP")).prune()
    print "prune np"
    print tmp.pt()
    