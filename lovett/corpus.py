__docformat__ = "restructuredtext en"

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
