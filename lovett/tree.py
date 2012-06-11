import nltk.tree as T

__docformat__ = "restructuredtext en"

class LovettTree(T.ParentedTree):
    """A class that wraps a ``nltk.tree.ParentedTree``.

    Currently it does not do much.

    """
    def __unicode__(self, indent = 0):
        if len(self) == 1 and isinstance(self[0], basestring):
            # This is a leaf node
            # TODO: python3 compat of isinstance, string formatting
            return u"(%s %s)" % (unicode(self.node), unicode(self[0]))
        else:
            s = u"(%s " % (unicode(self.node))
            l = len(s)
            # lstrip is to whack the initial newline+spaces
            leaves = (u"\n" + u" " * (indent + l)).join(map(lambda x: x.__unicode__(indent + l), self))
            return u"%s%s%s" % (s, leaves, u")")

    def __str__(self, indent = 0):
        return str(self.__unicode__(indent))
        
