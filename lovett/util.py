import sys # for debugging only
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
    return reduce(max, map(indexOfTree, tree.subtrees()))

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
    return isLeafNode(t) and t.text in ["*T*","*ICH*","*CL*","*"]

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
    r ="(" + name + " "
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
