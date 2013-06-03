from __future__ import unicode_literals

import abc

__docformat__ = "restructuredtext en"

class AbstractCodingQuery(metaclass=abc.ABCMeta):
    def __init__(self, name, desc):
        if name is None:
            raise Exception("Must supply a name for the coding query.")
        self.name = name
        self.description = desc


    @abstractmethod
    def code_tree(self, tree):
        pass

class CodingQuery(AbstractCodingQuery):
    def __init__(self, name, mapping, desc = ""):
        super(CodingQuery, self).__init__(name, desc)
        self.mapping = mapping

    def code_tree(self, tree):
        for key, fn in self.mapping:
            if fn(tree):
                return key


class FunctionCodingQuery(AbstractCodingQuery):
    def __init__(self, name, fn, desc = ""):
        super(CodingQuery, self).__init__(name, desc)
        self.fn = fn

    def code_tree(self, tree):
        return self.fn(tree)
