import lovett
import lovett.io
import lovett.util
import lovett.tree_new

import collections
import collections.abc
import copy
import re
import concurrent.futures

__docformat__ = "restructuredtext en"

# TODO: file-backed option -- never reads trees into memory, uses temp
# files to process one-by-one

class CorpusIterator(collections.abc.Iterator):
    def __init__(self, corpus, sequence_iter):
        self.corpus = corpus
        self.si = sequence_iter

    def __iter__(self):
        return self

    def __next__(self):
        n = self.si.__next__()
        return n.inCorpus(self.corpus)

class Corpus(collections.abc.MutableSequence):
    """A class to represent a corpus: a list of trees and associated
    metadata.

    """

    # Constructors
    def __init__(self, metadata, trees, version="old-style"):
        """Create a corpus.

        :param metadata: metadata associated with this corpus
        :type metadata: dict
        :param trees: the trees in the corpus
        :type trees: list of `LovettTree`

        """
        self.metadata = metadata or {}
        self.trees = trees
        self.version = version
        # TODO: read codes from corpussearch?
        self.coders = collections.OrderedDict()

        for t in self.trees:
            t.corpus = self

    @classmethod
    def fromTrees(cls, trees, metadata=None, **kwargs):
        # TODO: potentially expensive...is this right?
        return cls(metadata, copy.deepcopy(trees), **kwargs)

    @classmethod
    def fromFile(cls, file, version="old-style"):
        # TODO: optimize
        with open(file) as f:
            trees = re.compile("\n\n+").split(f.read())
        m = lovett.new_tree.parse(trees[0], version=version)
        if m.label == "METADATA":
            meta = lovett.util._treeToDict(m)
            return cls(meta, trees[1:])
        else:
            return cls(None, trees)

    @classmethod
    def fromFiles(cls, files, version="old-style"):
        # TODO: optimize
        trees = ""
        for file in files:
            with open(file) as f:
                trees += re.compile("\n\n+").split(f.read())
                # TODO: mutliple files with their metadata...
        m = lovett.new_tree.parse(trees[0], version)
        if m.label == "METADATA":
            meta = lovett.util._treeToDict(m)
            return cls(meta, trees[1:])
        else:
            return cls(None, trees)

    # ABC methods
    def __contains__(self, arg):
        return self.trees.__contains__(arg)

    def __iter__(self):
        return self.trees.__iter__()

    def __len__(self):
        return len(self.trees)

    def __getitem__(self, index):
        return self.trees[index]

    def __setitem__(self, index, value):
        self.trees[index] = value

    def __delitem__(self, index):
        del self.trees[index]

    def insert(self, index, value):
        return self.trees.insert(index, value)

    # Instance methods
    def write(self, fil):
        """Write the corpus.

        :param fil: a file object to write to, or the name of a
        file to open for writing
        :type fil: string of ``file`` object

        """
        if isinstance(fil, str):
            fil = open(fil, "w")
        lovett.io.writeTrees(self.metadata, self.trees, fil)

    def _mapTrees(self, fn):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            self.trees = executor.map(fn, self.trees)

    def addCoder(self, coder):
        self.coders[coder.name] = coder

    def addCoders(self, coders):
        for coder in coders:
            self.addCoder(coder)
