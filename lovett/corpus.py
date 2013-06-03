import lovett
import lovett.io
import lovett.util
import lovett.tree_new

import collections
import collections.abc
import copy
import re
import concurrent.futures
import itertools

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
    def __init__(self, metadata, trees):
        """Create a corpus.

        :param metadata: metadata associated with this corpus
        :type metadata: dict
        :param trees: the trees in the corpus
        :type trees: list of `Root`

        """
        self.metadata = metadata or {}
        # TODO: we should not need that, but somehow blank (None) trees slip in
        self.trees = list((t for t in trees if t))
        # TODO: read codes from corpussearch?
        self.coders = collections.OrderedDict()

        for t in self.trees:
            t.corpus = self

    @classmethod
    def fromTrees(cls, trees, metadata=None):
        # TODO: potentially expensive...is this right?
        return cls(metadata, copy.deepcopy(trees))

    @classmethod
    def fromTreeStrings(cls, trees, metadata=None):
        fmt = metadata.get('FORMAT') if metadata else 'old-style'
        with concurrent.futures.ProcessPoolExecutor() as exc:
            return cls(metadata, exc.map(lovett.tree_new.parse, trees,
                                         itertools.repeat(fmt)))

    @classmethod
    def fromFile(cls, file, format="old-style"):
        # TODO: optimize
        with open(file) as f:
            trees = re.compile("\n\n+").split(f.read())
        m = lovett.tree_new.parse(trees[0])
        if m.tree.label == "VERSION":
            meta = lovett.util._treeToDict(m)['VERSION']
            return cls.fromTreeStrings(trees[1:], meta)
        else:
            return cls.fromTreeStrings(trees)

    @classmethod
    def fromFiles(cls, files, format="old-style"):
        # TODO: optimize
        trees = []
        for file in files:
            with open(file) as f:
                trees.extend(re.compile("\n\n+").split(f.read()))
        # TODO: mutliple files with their metadata...
        m = lovett.tree_new.parse(trees[0])
        if m.tree.label == "VERSION":
            meta = lovett.util._treeToDict(m)
            return cls.fromTreeStrings(trees[1:], meta)
        else:
            return cls.fromTreeStrings(trees)

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
        fil.write("( " + lovett.util.metadata_str(self.metadata, "VERSION") +
                  ")\n\n")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            strs = executor.map(str, self.trees)
        fil.write("\n\n".join(strs))
        fil.close()

    def _mapTrees(self, fn, *rest):
        # with concurrent.futures.ProcessPoolExecutor() as executor:
        #     self.trees = list(executor.map(fn, self.trees, *rest))
        self.trees = list(map(fn, self.trees, *rest))

    def addCoder(self, coder):
        self.coders[coder.name] = coder

    def addCoders(self, coders):
        for coder in coders:
            self.addCoder(coder)

    @property
    def words(self):
        count = 0
        for tree in self:
            for leaf in tree.pos:
                if lovett.util.is_word(leaf):
                    count += 1
        return count
