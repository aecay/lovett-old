import unittest
import cStringIO as StringIO
import textwrap

from lovett.tree import LovettTree
from lovett.corpus import Corpus
import lovett.io

class IOTest(unittest.TestCase):
    def test_treeToDict(self):
        t = LovettTree("((FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertEqual(lovett.io._treeToDict(t),
                         { "FOO" : "bar",
                           "BAZ" : { "QUUX" : "1",
                                     "BLORFLE" : "2"}})

    def test_parseVersionTree(self):
        t = LovettTree("""
                                   ( (VERSION (FORMAT dash)
                                              (SOMETHING else)))
                                   """)
        self.assertEqual(lovett.io._parseVersionTree(t),
                         { "FORMAT" : "dash",
                           "SOMETHING" : "else" })
        t = lovett.tree.LovettTree("((FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertIsNone(lovett.io._parseVersionTree(t))

    def test_dictToTrees(self):
        d = { 'foo' : 'bar',
              'baz' : { '1' : 'one',
                        '2' : 'two' } }
        self.assertEqual(lovett.io._dictToTrees(d),
                         [LovettTree("foo", ["bar"]),
                          LovettTree("baz", [LovettTree("1", ["one"]),
                                             LovettTree("2", ["two"])])])

    def test_dictToMetadata(self):
        d = { 'foo' : 'bar',
              'baz' : { '1' : 'one',
                        '2' : 'two' } }
        self.assertEqual(lovett.io._dictToMetadata(d),
                         LovettTree("METADATA", [LovettTree("foo", ["bar"]),
                                                 LovettTree("baz",
                                                            [LovettTree("1", ["one"]),
                                                             LovettTree("2", ["two"])])]))


    def test_readTrees(self):
        f = StringIO.StringIO(textwrap.dedent("""
                                              /*
                                              hello
                                              I am a comment.
                                              */
                                     
                                              /~*
                                              I am another
                                              *~/
                                              (IP (NP Foos) (V bar))
                                              
                                              <+ another comment +>
                                              
                                              
                                              (IP (NP Bazes) (V quux))
                                              
                                              
                                              
                                              
                                              <+ yay +>
                                              """).strip())
        self.assertEqual(lovett.io.readTrees(f, stripComments = True),
                         [LovettTree("(IP (NP Foos) (V bar))"),
                          LovettTree("(IP (NP Bazes) (V quux))")])

    def test_readCorpus(self):
        f = StringIO.StringIO(textwrap.dedent("""
                                              /*
                                              hello
                                              I am a comment.
                                              */
                                              ( (VERSION (FORMAT dash)))
                                              
                                              /~*
                                              I am another
                                              *~/
                                              (IP (NP Foos) (V bar))
                                              
                                              <+ another comment +>
                                              
                                              
                                              (IP (NP Bazes) (V quux))
                                              
                                              
                                              
                                              
                                              <+ yay +>
                                              """).strip())
        c = lovett.io.readCorpus(f, stripComments = True)
        self.assertEqual(c.metadata, { "FORMAT" : "dash" })
        self.assertEqual(c.trees,
                         [LovettTree("(IP (NP Foos) (V bar))"),
                          LovettTree("(IP (NP Bazes) (V quux))")])
