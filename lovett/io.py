import lovett.tree, lovett.corpus

def readTrees(f):
    current_tree = ""
    comment = False
    all_trees = []
    for l in f.readlines():
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
        elif l.strip() == "":
            # Found a blank line, the tree separator
            if current_tree.strip() != "":
                all_trees.append(lovett.tree.LovettTree(current_tree))
                current_tree = ""
        else:
            current_tree = current_tree + l
    if comment:
        # We should not reach the end of the file in a comment
        raise Exception(
            "End of file reached while in comment; possibly corrupt file!")
    else:
        return all_trees

def readCorpus(f):
    all_trees = readTrees(f)
    version_tree = all_trees[0]
    version_dict = _parseVersionTree(version_tree)
    if version_dict is None:
        # An old file, put the version back on the text
        return lovett.corpus.Corpus(None, all_trees)
    else:
        return lovett.corpus.Corpus(version_dict, all_trees[1:])

def _parseVersionTree(t):
    version = t[0]
    if version.node != "VERSION":
        return None
    return _treeToDict(t[0])

def _treeToDict(t):
    if isinstance(t[0], basestring):
        return t[0]
    else:
        return dict([(n.node, _treeToDict(n)) for n in t])