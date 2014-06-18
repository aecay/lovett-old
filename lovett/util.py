from functools import reduce
import re
import lxml.etree

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
    return reduce(_max_or_none, map(index, tree.subtrees()))

def set_index(tree, index):
    # TODO: do we allow mutating the return value of metadata()?
    tree.metadata()['index'] = index

def index(tree):
    return tree.metadata().get('index', None)

def index_type(tree):
    return tree.metadata().get('idxtype', None)

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
        del tree.metadata()['index']
    except KeyError:
        pass
    try:
        del tree.metadata()['idxtype']
    except KeyError:
        pass

def is_leaf(t):
    # TODO: remove in favor of shorter name
    return t.tag in ["text", "ec", "trace", "comment"]

def is_trace(t):
    return t.tag == "trace"

def is_ec(t):
    return t.tag == "ec"

def is_text(t):
    return t.tag == "text"

def iter_flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)) and not \
           isinstance(e, lxml.etree._Element):
            for f in iter_flatten(e):
                yield f
        else:
            yield e
