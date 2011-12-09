### Traces/movement indices
def getLargestIndex(tree):
    # TODO: this must be made to understand the new format, where I
    # think I want indices in METADATA
    return reduce(max, map(indexOfTree, tree.subtrees()))

def addIndexToTree(index, tree):
    # TODO: do dash-tags go inside or outside index?
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

def indexOfTree(tree):
    if isinstance(tree[0], str) and tree[0][0] == "*":
        # This is an EC
        temp = tree[0].split("-")
        ret = 0
        try:
            if len(temp) == 2 and temp[-1].isdigit():
                ret = int(temp[-1])
            elif len(temp) == 3 abd temp[-2].isdigit():
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

def removeIndexFromTree(tree):
    old_index = indexOfTree(tree)
    if isinstance(tree[0], str) and tree[0][0] == "*":
        # This is an EC
        temp = tree[0].split("-")
        try:
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
