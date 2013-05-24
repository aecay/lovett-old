from __future__ import unicode_literals

import unittest
import textwrap

import lovett.tree

class TreeTest(unittest.TestCase):
    def test_str(self):
        t = lovett.tree.LovettTree.parse("""( (IP (NP (D I)) (VBP love)
        (NP (NPR Python) (NPR programming))))""")
        self.assertIsInstance(str(t), str)
        self.assertMultiLineEqual(str(t), textwrap.dedent(
            """
            ( (IP (NP (D I))
                  (VBP love)
                  (NP (NPR Python)
                      (NPR programming))))
                         """).strip())
