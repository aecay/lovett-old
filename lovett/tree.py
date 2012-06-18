import nltk.tree

__docformat__ = "restructuredtext en"

def nextToken(s):
    s = s.lstrip()
    if s == "":
        raise Exception("ran out of input")
    if s[0] in "()":
        return s[0], s[1:]
    else:
        i = 1
        while s[i] not in " )\n\t":
            i += 1
        return s[0:i], s[i:]

def parseTree(s):
    stack = []
    while True:
        t, s = nextToken(s)
        if t == "(":
            n, s = nextToken(s)
            if n == "(":
                s = n + s
                n = ""
            stack.append(LovettTree(n, []))
        elif t == ")":
            p = stack.pop()
            if len(stack) == 0:
                if s.strip() == "":
                    return p
                else:
                    raise Exception("extra input: %s" % s)
            stack[-1].append(p)
        else:
            stack[-1].append(t)



class LovettTree(nltk.tree.ParentedTree):
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
        
