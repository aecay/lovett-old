import lovett.tree_new

from functools import reduce
import re

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
def _max_or_none(x, y):
    if x is None and y is None:
        return None
    if y is None:
        return x
    if x is None:
        return y
    return max(x, y)

def largest_index(tree):
    return reduce(_max_or_none, map(index, tree.subtrees))

def set_index(tree, index):
    tree.metadata['INDEX'] = index

def index(tree):
    return tree.metadata.get('INDEX', None)

def index_type(tree):
    return tree.metadata.get('IDX-TYPE', None)

def index_type_short(tree):
    it = index_type(tree)
    if it == "gap":
        return "="
    elif it == "regular":
        return "-"
    else:
        return None

def remove_index(tree):
    try:
        del tree.metadata['INDEX']
    except KeyError:
        pass
    try:
        del tree.metadata['IDX-TYPE']
    except KeyError:
        pass

def label_and_index(s):
    l = s.split("=")
    if len(l) > 2:
        raise ValueError("too many = signs in label: %s" % s)
    if len(l) > 1:
        if l[-1].isdigit():
            return "=".join(l[:-1]), "gap", int(l[-1])
    l = s.split("-")
    if len(l) > 1:
        if l[-1].isdigit():
            return "-".join(l[:-1]), "regular", int(l[-1])
        else:
            return s, None, None
    else:
        return s, None, None

def index_from_string(s):
    return label_and_index(s)[2]

def index_type_from_string(s):
    return label_and_index(s)[1]


def isLeafNode(t):
    # TODO: remove in favor of shorter name
    return isinstance(t, lovett.tree_new.Leaf)

isLeaf = isLeafNode

def isTrace(t):
    # TODO: the split below is a kludge; fix it
    return isLeafNode(t) and \
        t.text.split("-")[0] in ["*T*", "*ICH*", "*CL*", "*", "*con*"]

def isEC(t):
    # TODO: inexact
    # TODO: how can an empty text happen?!
    return isLeafNode(t) and (t.text == "0" or t.text == "" or
                              t.text[0] == "*")

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
    elif isinstance(t, lovett.tree_new.Root):
        return _treeToDict(t.tree)
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

def metadata_str(dic, name="METADATA", indent=0):
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

def _shouldIndexLeaf(tree):
    # TODO: split is a kludge, remove
    return re.split("[-=]", tree.label)[0] in ["*T*", "*ICH*", "*CL*", "*"]

def is_word(tree):
    if tree.label in ["CODE", ".", ",", "FW"]:
        return False
    if tree.text[0] in ["*", "@"]:
        return False
    return True
