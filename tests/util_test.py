import unittest
from io import StringIO
import textwrap

from lovett.tree import LovettTree
from lovett.corpus import Corpus
import lovett.util

class UtilTest(unittest.TestCase):
    def test_treeToDict(self):
        t = LovettTree.parse("((FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertEqual(lovett.util._treeToDict(t),
                         { "FOO" : "bar",
                           "BAZ" : { "QUUX" : "1",
                                     "BLORFLE" : "2"}})

    def test_parseVersionTree(self):
        t = LovettTree.parse("""
                                   ( (VERSION (FORMAT dash)
                                              (SOMETHING else)))
                                   """)
        self.assertEqual(lovett.util._parseVersionTree(t),
                         { "FORMAT" : "dash",
                           "SOMETHING" : "else" })
        t = LovettTree.parse("((FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertIsNone(lovett.util._parseVersionTree(t))

    # def test_dictToTrees(self):
    #     d = { 'foo' : 'bar',
    #           'baz' : { '1' : 'one',
    #                     '2' : 'two' } }
    #     self.assertEqual(lovett.util._dictToTrees(d),
    #                      [LovettTree("foo", ["bar"]),
    #                       LovettTree("baz", [LovettTree("1", ["one"]),
    #                                          LovettTree("2", ["two"])])])

    # def test_dictToMetadata(self):
    #     d = { 'foo' : 'bar',
    #           'baz' : { '1' : 'one',
    #                     '2' : 'two' } }
    #     self.assertEqual(lovett.util._dictToMetadata(d),
    #                      LovettTree("METADATA", [LovettTree("foo", ["bar"]),
    #                                              LovettTree("baz",
    #                                                         [LovettTree("1", ["one"]),
    #                                                          LovettTree("2", ["two"])])]))
