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
        raise Exception("unbalanced comment")
    return r

def strip(s):
    return s.strip()
def parse(s):
    return lovett.tree.LovettTree.parse(s)

def readTrees(f, stripComments = False, parallel = True):
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
    sys.stderr.write("parallel is: %s\n" % parallel)
    if parallel:
        p = multiprocessing.Pool()
        trees = p.map(strip, trees)
        trees = filter(lambda s: s != "", trees)
        trees = p.map(parse, trees)
    else:
        trees = map(lambda s: s.strip(), trees)
        trees = filter(lambda s: s != "", trees)
        trees = map(lovett.tree.LovettTree.parse, trees)
    return trees

def writeTrees(metadata, trees, file):
    # TODO: if trees are nltk trees (not strings), this barfs
    """Write trees to file.

    :param metadata: the metadata for these trees, or ``None``
    :param trees: a list of trees
    :param file: the file to write to

    """
    if metadata:
        file.write(_dictToMetadata(metadata) + "\n\n")
    if isinstance(trees[0], lovett.tree.LovettTree):
        trees = map(unicode, trees)
    file.write("\n\n".join(trees))
