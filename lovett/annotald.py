import sys
import transformer as TT
import nltk.tree as T
import subprocess

def flagIf(expr):
    def _flagIfInner(version, trees):
        trees = trees.replace("-FLAG", "")
        trees = trees.split("\n\n")
        results = []
        for tree in trees:
            trans = TT.TreeTransformer(T.ParentedTree(tree))
            trans.findNodes(expr)
            trans.changeLabel(lambda x: x + "-FLAG")
            results.append(trans.pt())
        return '\n\n'.join(results)
    return _flagIfInner


def stdinValidator(path):
    def _stdinValidator(version, trees):
        print "path is: " + path
        proc = subprocess.Popen(path,
                                stdin = subprocess.PIPE,
                                stdout = subprocess.PIPE)
        out = proc.communicate(input = trees.encode('utf-8'))[0]
        print "out is: " + out.decode('utf-8')
        return out.decode('utf-8')
    return _stdinValidator
