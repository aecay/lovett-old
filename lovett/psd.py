from lxml.builder import ElementMaker
from .corpus import parser
from .tree import Tree as PsdTree
import re

E = ElementMaker(makeelement=parser.makeelement)

def parse_psd_string(s):
    corpus = E.corpus()
    trees = s.split("\n\n")
    for tree in trees:
        parsed_tree = PsdTree(tree)
        sentence = E.sentence()
        for node in parsed_tree:
            if node.node == "ID":
                sentence.set_id(node[0])
            elif node.node == "METADATA":
                m = _parse_metadata(node)
                sentence.insert(m, 0)
            else:
                # TODO: barf if there are multiple nodes
                sentence.append(_parse_node(node))

def _parse_metadata(m):
    node = E("meta")
    for s in m:
        node.append(_parse_meta_inner(s))
    return node

def _parse_meta_inner(m):
    if isinstance(m, (str)):
        return m
    else:
        node = E(m.node)
        for s in m:
            node.append(_parse_meta_inner(s))
        return node

def _parse_node(n):
    if isinstance(n[0], (str)):
        # terminal node
        return _parse_terminal(n)
    else:
        node = E.nonterminal()
        m = node.metadata()
        pieces = n.node.split("-")
        try:
            idx = int(pieces[-1])
            pieces.pop()
            m["index"] = str(idx)
        except ValueError:
            pass
        node.attrib["category"] = pieces[0]
        # TODO: validate subcategories
        if len(pieces) > 1:
            node.attrib["subcategory"] = pieces[1]
        if len(pieces) > 2:
            raise PsdParseError("Too many dash tags: %s" % pieces)
        return node

def _parse_terminal(n):
    t = n[0]
    pieces = re.split("[-=]", t)
    node_pieces = re.split("[-=]", n.node)
    tt = pieces[0]

    def oblig_index(tag_):
        try:
            idx = int(pieces[-1])
        except ValueError:
            raise PsdParseError("noninteger index for A movement trace: " + t)
        pieces.pop()
        tag_.metadata()["index"] = str(idx)
        tag_.metadata()["idxtype"] = "gap" if "=" in t else "regular"

    def optional_index(tag_):
        try:
            idx = int(node_pieces[-1])
            node_pieces.pop()
            tag_.metadata()["index"] = str(idx)
            tag_.metadata()["idxtype"] = "gap" if "=" in n.node else "regular"
        except ValueError:
            pass

    def cat_subcat(tag_):
        tag_.set("category", node_pieces[0])
        if len(node_pieces) > 1:
            tag_.set("subcategory", node_pieces[1])
        if len(node_pieces) > 2:
            raise PsdParseError("Too many dash tags: %s" % node_pieces)

    if tt[0] == "*":
        if tt == 1:
            # "*", A-movement trace
            tag = E.trace()
            oblig_index(tag)
            cat_subcat(tag)
            tag.attrib["tracetype"] = "amovt"
        elif t[1].islower():
            # "*abc*", empty category
            tag = E.ec()
            optional_index(tag)
            cat_subcat(tag)
            tag.attrib["ectype"] = tt[1:-1]
        else:
            # "*X*", A-bar trace
            tag = E.trace()
            oblig_index(tag)
            cat_subcat(tag)
            tag.attrib["tracetype"] = tt[1:-1]
    elif t == "0":
        tag = E.ec()
        optional_index(tag)
        cat_subcat(tag)
        tag.attrib["ectype"] = "zero"
    elif t.node == "CODE":
        tag = E.comment()
        # TODO: comment type
    else:
        # TODO: lemmas etc.
        tag = E.text()
        optional_index(tag)
        cat_subcat(tag)

    return tag

class PsdParseError(Exception):
    pass
