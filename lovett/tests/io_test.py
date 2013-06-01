import unittest
from io import StringIO
import textwrap

from lovett.tree import LovettTree
from lovett.corpus import Corpus
import lovett.io

class IOTest(unittest.TestCase):
    pass
    # def test_readTrees(self):
    #     f = StringIO(textwrap.dedent("""
    #     /*
    #     hello
    #     I am a comment.
    #     */

    #     /~*
    #     I am another
    #     *~/
    #     (IP (NP Foos) (V bar))

    #     <+ another comment +>


    #     (IP (NP Bazes) (V quux))




    #     <+ yay +>
    #     """).strip())
    #     self.assertEqual(lovett.io.readTrees(f, stripComments = True),
    #                      [LovettTree.parse("(IP (NP Foos) (V bar))"),
    #                       LovettTree.parse("(IP (NP Bazes) (V quux))")])

    # TODO: move to tree test
    # def test_readCorpus(self):
    #     f = StringIO.StringIO(textwrap.dedent("""
    #     /*
    #     hello
    #     I am a comment.
    #     */
    #     ( (VERSION (FORMAT dash)))

    #     /~*
    #     I am another
    #     *~/
    #     (IP (NP Foos) (V bar))

    #     <+ another comment +>


    #     (IP (NP Bazes) (V quux))




    #     <+ yay +>
    #     """).strip())
    #     c = lovett.io.readCorpus(f, stripComments = True)
    #     self.assertEqual(c.metadata, { "FORMAT" : "dash" })
    #     self.assertEqual(c.trees,
    #                      [LovettTree("(IP (NP Foos) (V bar))"),
    #                       LovettTree("(IP (NP Bazes) (V quux))")])
