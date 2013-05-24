import lovett.io
import lovett.util
import multiprocessing
import codecs

__docformat__ = "restructuredtext en"

# TODO: file-backed option -- never reads trees into memory, uses temp
# files to process one-by-one

class Corpus:
    """A class to represent a corpus: a list of trees and associated
    metadata.

    """
    def __init__(self, metadata, trees, parallel = True):
        """Create a corpus.

        :param metadata: metadata associated with this corpus
        :type metadata: dict
        :param trees: the trees in the corpus
        :type trees: list of `LovettTree`

        """
        self.metadata = metadata
        self.trees = trees
        # TODO: read codes from corpussearch?
        self.codes = {}
        self.parallel = parallel


    def write(self, file_or_name):
        """Write the corpus.

        :param file_or_name: a file object to write to, or the name of a
        file to open for writing

        """
        if not isinstance(file_or_name, file):
            file_or_name = codecs.open(file_or_name, "w", "utf-8")
        lovett.io.writeTrees(self.metadata, self.trees, file_or_name)


    def _mapTrees(self, fn):
        if self.parallel:
            p = multiprocessing.Pool()
            return p.map(fn, self.trees)
        else:
            return map(fn, self.trees)

    def code(query):
        def do_coding(tree):
            return query.codeTree(tree)
        self.codes[query.name] = self._mapTrees(do_coding)

    def print_codes(fil, *args):
        if len(args) == 0:
            args = self.codes.keys()
        with codecs.open(fil, "w", "utf-8") as f:
            f.write(":".join(args))
            f.write("\n")
            for i in xrange(0, len(self.trees)):
                # The efficiency gods are angry.
                for c in self.codes.itervalues():
                    f.write(c[i])
                f.write("\n")

    @classmethod
    def fromFiles(cls, files, stripComments = False, parallel = True):
        """Read a `Corpus` from some files.

        The files' VERSION trees must match, up to inofrmation that is
        file-specific (such as the HASH).

        :param files: the files to read from
        :type files: strings or files
        :param stripComments: whether to remove CorpusSearch comments from `files`
        :type stripComments: Boolean

        """
        all_trees = []
        version = {}
        for f in files:
            if not isinstance(f, file):
                f = codecs.open(f, "r", "utf-8")
            trees = lovett.io.readTrees(f, stripComments, parallel)
            vd = lovett.util._parseVersionTree(trees[0])
            if vd is not None:
                version = lovett.util._unifyVersionTrees(version, vd)
                trees = trees[1:]
            all_trees.extend(trees)
        return cls(version, all_trees, parallel = parallel)
