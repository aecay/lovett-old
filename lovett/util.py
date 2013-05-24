import sys # for debugging only
import lovett.tree

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
                return int(temp[-1])
            # TODO: how can this ever happen?
            elif len(temp) == 3 and temp[-2].isdigit():
                return int(temp[-2])
        if "=" in tree.node:
            temp = tree.node.split("=")
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


def isLeafNode(t):
    if not isinstance(t[0], lovett.tree.Tree):
        return True
    else:
        return False

def isTrace(t):
    return isLeafNode(t) and (t[0][0:3] == "*T*" or
                              t[0][0:5] == "*ICH*" or
                              t[0][0:4] == "*CL*")

def iter_flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)) and not isinstance(e, lovett.tree.Tree):
            for f in iter_flatten(e):
                yield f
        else:
            yield e


# From nltk.internals
def slice_bounds(sequence, slice_obj, allow_step=False):
    """
    Given a slice, return the corresponding (start, stop) bounds,
    taking into account None indices and negative indices.  The
    following guarantees are made for the returned start and stop values:

      - 0 <= start <= len(sequence)
      - 0 <= stop <= len(sequence)
      - start <= stop

    :raise ValueError: If ``slice_obj.step`` is not None.
    :param allow_step: If true, then the slice object may have a
        non-None step.  If it does, then return a tuple
        (start, stop, step).
    """
    start, stop = (slice_obj.start, slice_obj.stop)

    # If allow_step is true, then include the step in our return
    # value tuple.
    if allow_step:
        step = slice_obj.step
        if step is None: step = 1
        # Use a recursive call without allow_step to find the slice
        # bounds.  If step is negative, then the roles of start and
        # stop (in terms of default values, etc), are swapped.
        if step < 0:
            start, stop = slice_bounds(sequence, slice(stop, start))
        else:
            start, stop = slice_bounds(sequence, slice(start, stop))
        return start, stop, step

    # Otherwise, make sure that no non-default step value is used.
    elif slice_obj.step not in (None, 1):
        raise ValueError('slices with steps are not supported by %s' %
                         sequence.__class__.__name__)

    # Supply default offsets.
    if start is None: start = 0
    if stop is None: stop = len(sequence)

    # Handle negative indices.
    if start < 0: start = max(0, len(sequence)+start)
    if stop < 0: stop = max(0, len(sequence)+stop)

    # Make sure stop doesn't go past the end of the list.  Note that
    # we avoid calculating len(sequence) if possible, because for lazy
    # sequences, calculating the length of a sequence can be expensive.
    if stop > 0:
        try: sequence[stop-1]
        except IndexError: stop = len(sequence)

    # Make sure start isn't past stop.
    start = min(start, stop)

    # That's all folks!
    return start, stop

def _parseVersionTree(t):
    """Parse a version tree.

    A version tree must have the form:

    ::

      ( (VERSION (KEY1 val1)
                 (KEY2 (SUBKEY1 val1))))

    :param t: the version tree to parse
    :type t: `LovettTree`

    """
    version = t[0]
    if version.node != "VERSION":
        return None
    return _treeToDict(t[0])

def _treeToDict(t):
    """Convert a `LovettTree` to a dictionary.

    Each key in the dictionary corresponds to a node label from the
    tree; each value is either a string (leaf node) or another dict
    (recursive node.)

    """
    if isinstance(t[0], str):
        return t[0]
    else:
        return dict([(n.node, _treeToDict(n)) for n in t])

def _dictToMetadata(d):
    if not d:
        return None
    return lovett.tree.LovettTree("METADATA", _dictToTrees(d))


def _dictToTrees(d):
    if isinstance(d, str):
        return [d]
    r = []
    for k in d:
        r.append(lovett.tree.LovettTree(k, _dictToTrees(d[k])))
        return r

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
    r ="(" + name + " "
    l = len(r)
    def helper(d, k):
        if isinstance(d[k], str):
            return "(" + k + " " + d[k] + ")"
        else:
            return metadata_str(d[k], k, indent + l)
    r += ("\n" + " " * (indent + l)).join(
        helper(dic, key) for key in sorted(dic.keys())
    )
    r += ")"
    return r
