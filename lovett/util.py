import sys # for debugging only

### String representation of trees
def printTree(tree, indent = 0):
    if len(tree) == 1 and isinstance(tree[0], str):
        # This is a leaf node
        # TODO: python3 compat of isinstance, string formatting
        return "\n%s(%s %s)" % (" " * indent, tree.node, tree[0])
    else:
        s = "%s(%s " % (" " * indent, tree.node)
        l = len(s)
        # lstrip is to whack the initial newline+spaces
        leaves = "".join(map(lambda x: printTree(x, indent + l), tree)).lstrip()
        return s + leaves + ")"

### Tree validation
# TODO: this fn is untested
def validateIndices(tree):
    indices = []
    for leaf in tree.leaves():
        idx = indexOfTree(leaf)
        if indices[idx]:
            indices[idx] = indices[idx] + 1
        else:
            indices[idx] = 1
    valid = True
    for i in indices:
        if not indices[i] or indices[i] == 1:
            valid = False
    return valid

def validateTagset(tree, tags, dashes):
    # TODO: Idea: allow passing a list of lists, like:
    # [ ["NP", "-OB1", "-OB2", ...],
    #   ...
    #   ] <-- or maybe use a dict?
    # Convert this into a grammar (peg style) and validate against it.
    # Also: separate tagsets for leaves and non-terminals
    pass

### Traces/movement indices
def getLargestIndex(tree):
    # TODO: this must be made to understand the new format, where I
    # think I want indices in METADATA
    return reduce(max, map(indexOfTree, tree.subtrees()))

def addIndexToTree(index, tree):
    # TODO: do dash-tags go inside or outside index?
    try:
        if isinstance(tree[0], str) and tree[0][0] == "*":
            # This is an EC; so add index to the leaf
            temp = tree[0].split("-")
            # This is a bogus test for the presence of a lemma, in general.  But
            # traces should not contain dashes, so it is OK here.
            if len(temp) == 1:
                temp.append(str(index))
            else:
                temp.insert(-1, str(index))
            tree[0] = "-".join(temp)
        else:
            # not EC; add index to the label
            tree.node = tree.node + "-" + str(index)
    except IndexError:
        sys.stderr.write("idxerr, tree is: %s" % tree)

def indexOfTree(tree):
    try:
        if isinstance(tree[0], str) and tree[0][0] == "*":
            # This is an EC
            temp = tree[0].split("-")
            ret = 0
            if len(temp) == 2 and temp[-1].isdigit():
                ret = int(temp[-1])
            elif len(temp) == 3 and temp[-2].isdigit():
                ret = int(temp[-2])
            return ret
        else:
            temp = tree.node.split("-")
            ret = 0
            try:
                ret = int(temp[-1])
            except ValueError:
                pass
            return ret
    except IndexError:
        sys.stderr.write("idxerr, tree is: %s" % tree)


def removeIndexFromTree(tree):
    old_index = indexOfTree(tree)
    if isinstance(tree[0], str) and tree[0][0] == "*":
        # This is an EC
        temp = tree[0].split("-")
        if len(temp) == 2 and temp[-1].isdigit():
            temp.pop()
        elif len(temp) == 3 and temp[-2].isdigit():
            temp.pop(-2)
        tree[0] = temp.join("-")
    else:
        temp = tree.node.split("-")
        ret = 0
        if temp[-1].isdigit():
            temp.pop()
        tree.node = temp.join("-")
    return old_index
