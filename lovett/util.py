import lovett.tree_new

from functools import reduce

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
    return reduce(max, map(indexOfTree, tree.subtrees))

def addIndexToTree(index, tree):
    tree.metadata['INDEX'] = index

def indexOfTree(tree):
    return tree.metadata.get('INDEX', 0)


def removeIndexFromTree(tree):
    del tree.metadata['INDEX']
    del tree.metadata['IDX-TYPE']


def isLeafNode(t):
    return isinstance(t, lovett.tree_new.Leaf)


def isTrace(t):
    return isLeafNode(t) and t.text in ["*T*", "*ICH*", "*CL*", "*"]

def iter_flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)) and not \
           isinstance(e, lovett.tree.Tree):
            for f in iter_flatten(e):
                yield f
        else:
            yield e

def _parseVersionTree(t):
    """Parse a version tree.

    A version tree must have the form:

    ::

      ( (VERSION (KEY1 val1)
                 (KEY2 (SUBKEY1 val1))))

    :param t: the version tree to parse
    :type t: `LovettTree`

    """
    if not isinstance(t, lovett.tree_new.Root):
        raise ValueError("pass a Root tree to _parseVersionTree: %r" % t)
    version = t.tree
    if version.label != "VERSION":
        return None
    return _treeToDict(t[0])

def _treeToDict(t):
    """Convert a `LovettTree` to a dictionary.

    Each key in the dictionary corresponds to a node label from the
    tree; each value is either a string (leaf node) or another dict
    (recursive node.)

    """
    if isinstance(t, lovett.tree_new.Leaf):
        return t.text
    else:
        return dict([(n.label, _treeToDict(n)) for n in t])

UNIFY_VERSION_IGNORE_KEYS = ["HASH"]

def _unifyVersionTrees(old, new):
    for k in new.keys():
        if k in UNIFY_VERSION_IGNORE_KEYS:
            continue
        if k in old:
            if old[k] == new[k]:
                pass
            else:
                raise Exception("Mismatched version info")
        else:
            old[k] = new[k]
    return old

def metadata_str(dic, name, indent):
    r = "(" + name + " "
    l = len(r)

    def helper(d, k):
        if not isinstance(d[k], dict):
            return "(" + k + " " + str(d[k]) + ")"
        else:
            return metadata_str(d[k], k, indent + l)
    r += ("\n" + " " * (indent + l)).join(
        helper(dic, key) for key in sorted(dic.keys())
    )
    r += ")"
    return r
