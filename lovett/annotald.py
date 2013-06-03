from __future__ import unicode_literals
import sys
import lovett.cs.transformer as TT
import lovett.tree_new as T
import lovett.corpus
import subprocess
import itertools
import lovett.cs.searchfns

def _flagIfHelper(tree, expr):
    trans = TT.TreeTransformer(tree)
    trans.findNodes(lovett.cs.searchfns.isLeaf())
    # for m in trans.matches():
    #     print(m.metadata)
    trans.findNodes(expr)
    trans.changeLabel(lambda x: x + "-FLAG")
    return trans._tree

def flagIf(expr):
    def _flagIfInner(version, trees):
        print(version)
        trees = trees.replace("-FLAG", "")
        trees = trees.split("\n\n")
        corpus = lovett.corpus.Corpus.fromTreeStrings(trees, version)
        corpus._mapTrees(_flagIfHelper, itertools.repeat(expr))
        print(str(corpus.trees[2]))
        r = '\n\n'.join(map(str, corpus.trees))
        return r
    return _flagIfInner


def stdinValidator(path):
    def _stdinValidator(version, trees):
        print("path is: " + path)
        proc = subprocess.Popen(path,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        out = proc.communicate(input=trees.encode('utf-8'))[0]
        print("out is: " + out.decode('utf-8'))
        return out.decode('utf-8')
    return _stdinValidator
