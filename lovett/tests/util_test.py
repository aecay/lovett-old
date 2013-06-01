import unittest
from io import StringIO
import textwrap

import lovett.tree_new
import lovett.util

class UtilTest(unittest.TestCase):
    def test_treeToDict(self):
        t = lovett.tree_new.parse("(METADATA (FOO bar) (BAZ (QUUX 1) (BLORFLE 2)))")
        self.assertEqual(lovett.util._treeToDict(t),
                         { "FOO" : "bar",
                           "BAZ" : { "QUUX" : "1",
                                     "BLORFLE" : "2"}})

    def test_parseVersionTree(self):
        t = lovett.tree_new.parse("""
                                   ( (VERSION (FORMAT dash)
                                              (SOMETHING else)))
                                   """)
        self.assertEqual(lovett.util._parseVersionTree(t),
                         { "FORMAT" : "dash",
                           "SOMETHING" : "else" })
        t = lovett.tree_new.parse("( (FOO (FOO bar) (BAZ (QUUX 1) (BLORFLE 2))))")
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
