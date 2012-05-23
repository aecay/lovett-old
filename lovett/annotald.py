import sys
import transformer as TT
import nltk.tree as T

# def flagIf(expr):
#     data = sys.stdin.read()
#     data = data.replace("-FLAG", "") # TODO: do this in a smarter way
#     trees = data.split("\n\n")
#     for tree in trees:
#         trans = TT.TreeTransformer(T.ParentedTree(tree))
#         trans.findNodes(expr)
#         trans.changeLabel(lambda x: x + "-FLAG")
#         print trans.pt() + "\n\n"
#     sys.stdout.close()

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
