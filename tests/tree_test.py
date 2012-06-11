import unittest
import textwrap

import lovett.tree

class TreeTest(unittest.TestCase):
    def test_str(self):
        t = lovett.tree.LovettTree("""( (IP (NP (D I)) (VBP love)
                                   (NP (NPR Python) (NPR programming))))""")
        self.assertIsInstance(str(t), str)
        self.assertMultiLineEqual(str(t), textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming))))
                         """).strip())

    def test_unicode(self):
        t = lovett.tree.LovettTree("""( (IP (NP (D I)) (VBP love)
                                   (NP (NPR Python) (NPR programming))))""")
        self.assertIsInstance(unicode(t), unicode)
        self.assertMultiLineEqual(unicode(t), textwrap.dedent(
            u"""
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming))))
                         """).strip())
