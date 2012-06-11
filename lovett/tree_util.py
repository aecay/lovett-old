import sys
import nltk.tree
import hashlib

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

def readTrees(f):
    current_tree = ""
    comment = False
    all_trees = []
    for l in f.readlines():
        if l.startswith("/*") or l.startswith("/~*"):
            # This begins a CorpusSearch comment
            comment = True
        elif comment:
            # Already in a comment, discard the line
            pass
        elif l.startswith("<+"):
            # A parser-mode comment, one line only
            pass
        elif l.endswith("*/\n") or l.endswith("*~/\n"):
            comment = False
        elif l.strip() == "":
            # Found a blank line, the tree separator
            if current_tree.strip() != "":
                all_trees = all_trees.append(nltk.tree.ParentedTree(current_tree))
                current_tree = ""
        else:
            current_tree = current_tree + l
    if comment:
        # We should not reach the end of the file in a comment
        raise Error("End of file reached while in comment; possible corrpution!")
    else:
        return all_trees

def readCorpus(f):
    all_trees = readTrees(f)
    version_tree = all_trees[0]
    text_trees = all_trees[1:]
    version_dict = parseVersionTree(version_tree)
    if version_dict is None:
        # An old file, put the version back on the text
        return (None, [version_tree] + text_trees)
    else:
        return (version_dict, text_trees)

def parseVersionTree(t):
    version = t[0]
    if version.node != "VERSION":
        return None
    d = {}
    for n in version:
        # TODO: is this error-proof/flexible enough?
        d[n.node] = n[0]
    return d

def isEmpty(tuple):
    if tuple[0] == "CODE":
        return True
    elif tuple[1][0] == "*" or \
            (tuple[1] == "0" and tuple[0] != "NUM"):
        return True
    return False

def hashCorpus(corpus):
    out = ""
    if corpus[0][0].node == "VERSION":
        trees = trees[1:]
    for t in corpus:
        w = map(lambda x: x[1], filter(lambda x: not isEmpty(x), t.pos()))
        out += "\n".join(w)
    h = hashlib.md5()
    h.update(out)
    return h.hexdigest()
