from __future__ import unicode_literals

import lovett.cs.transformer as TT
import lovett.corpus


def _flagIfHelper(tree, expr):
    trans = TT.TreeTransformer(tree)
    trans.findNodes(expr)
    if len(trans.matches()) > 0:
        trans.changeLabel(lambda x: x + "-FLAG")
    return trans.tree()

def flagIf(expr):
    def _flagIfInner(version, trees):
        trees = trees.replace("-FLAG", "")
        trees = trees.split("\n\n")
        c = lovett.corpus.Corpus.fromTreeStrings(trees, version)
        c._mapTrees(lambda x: _flagIfHelper(x, expr))
        r = '\n\n'.join(map(str, c.trees))
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
