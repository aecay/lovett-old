import lovett.io
import multiprocessing

__docformat__ = "restructuredtext en"

# TODO: file-backed option -- never reads trees into memory, uses temp
# files to process one-by-one

class Corpus:
    """A class to represent a corpus: a list of trees and associated
    metadata.

    """
    def __init__(self, metadata, trees):
        """Create a corpus.

        :param metadata: metadata associated with this corpus
        :type metadata: dict
        :param trees: the trees in the corpus
        :type trees: list of `LovettTree`

        """
        self.metadata = metadata
        self.trees = trees


    def write(self, file_or_name):
        """Write the corpus.

        :param file_or_name: a file object to write to, or the name of a
        file to open for writing

        """
        if isinstance(file_or_name, basestring):
            file_or_name = open(file_or_name, "w")
        lovett.io.writeTrees(self.metadata, self.trees, file_or_name)


    def eachTree(self, fn, parallel = True):
        if parallel:
            p = multiprocessing.Pool()
            self.trees = p.map(fn, self.trees)
        else:
            self.trees = map(fn, self.trees)
