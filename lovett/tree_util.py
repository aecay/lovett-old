import sys
import tree
import hashlib

def isEmpty(tuple):
    if tuple[1] == "CODE":
        return True
    elif tuple[0][0] == "*" or \
            (tuple[0] == "0" and tuple[1] != "NUM"):
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
