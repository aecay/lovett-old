from __future__ import unicode_literals

import lovett.tree, lovett.corpus

import sys
import multiprocessing

__docformat__ = "restructuredtext en"

def _stripComments(lines):
    r = []
    comment = False
    for l in lines:
        if l.startswith("/*") or l.startswith("/~*"):
            # This begins a CorpusSearch comment
            comment = True
        elif l.startswith("<+"):
            # A parser-mode comment, one line only
            pass
        elif l.endswith("*/\n") or l.endswith("*~/\n"):
            comment = False
        elif comment:
            # Already in a comment, discard the line
            pass
        else:
            r.append(l)
    if comment:
        raise Exception("unblaanced comment")
    return r

def readTrees(f, stripComments = False):
    """Read trees from a file.

    :param f: the file to read from
    :type f: file

    """
    current_tree = ""
    comment = False
    all_trees = []
    lines = f.readlines()
    if stripComments:
        lines = _stripComments(lines)
    trees = "".join(lines).split("\n\n")
    trees = map(lambda s: s.strip(), trees)
    trees = filter(lambda s: s != "", trees)
    trees = map(lovett.tree.LovettTree, trees)
    return trees

# TODO: move to Corpus class?
def readCorpus(f, stripComments = True):
    """Read a `Corpus` from a file.

    :param f: the file to read from
    :type f: file

    """
    all_trees = readTrees(f, stripComments)
    version_tree = all_trees[0]
    version_dict = _parseVersionTree(version_tree)
    if version_dict is None:
        # An old file, put the version back on the text
        return lovett.corpus.Corpus(None, all_trees)
    else:
        return lovett.corpus.Corpus(version_dict, all_trees[1:])

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
    if isinstance(t[0], basestring):
        return t[0]
    else:
        return dict([(n.node, _treeToDict(n)) for n in t])

def _dictToMetadata(d):
    return lovett.tree.LovettTree("METADATA", _dictToTrees(d))


def _dictToTrees(d):
    if isinstance(d, basestring):
        return [d]
    r = []
    for k in d:
        r.append(lovett.tree.LovettTree(k, _dictToTrees(d[k])))
    return r

def writeTrees(metadata, trees, file):
    """Write trees to file.

    :param metadata: the metadata for these trees, or ``None``
    :param trees: a list of trees
    :param file: the file to write to

    """
    if metadata:
        file.write(_dictToMetadata(metadata) + "\n\n")
    file.write("\n\n".join(trees))
