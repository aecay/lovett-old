from __future__ import unicode_literals

import lovett.tree
import lovett.corpus
import lovett.util

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


def parse(s):
    return lovett.tree.LovettTree.parse(s)


def writeTrees(metadata, trees, file):
    # TODO: if trees are nltk trees (not strings), this barfs
    """Write trees to file.

    :param metadata: the metadata for these trees, or ``None``
    :param trees: a list of trees
    :param file: the file to write to

    """
    if metadata:
        file.write(lovett.util._dictToMetadata(metadata) + "\n\n")
    if isinstance(trees[0], lovett.tree.LovettTree):
        trees = map(str, trees)
        file.write("\n\n".join(trees))
