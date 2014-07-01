from lxml.builder import ElementMaker
from .corpus import parser
from .psd_tree import Tree as PsdTree
import re

E = ElementMaker(makeelement=parser.makeelement)

def parse_psd_string(s, _type="psd"):
    """This function creates a corpus from a string of PSD-format trees separated
by single blank lines.

    :param str s: The string to process
    :param _type: Internal use only
    :returns: The corpus
    :rtype: :class:`lovett.corpus.corpus`

    """
    corpus = E.corpus()
    trees = s.split("\n\n")
    inserted = False
    for tree in trees:
        parsed_tree = PsdTree.parse(tree)
        sentence = E.sentence()
        corpus.append(sentence)
        for node in parsed_tree:
            if node.node == "ID":
                sentence.set_id(node[0])
            elif node.node == "METADATA":
                m = _parse_metadata(node)
                sentence.insert(m, 0)
            else:
                if inserted:
                    raise PsdParseException("Malformed tree:\n%s" % s)
                if _type == "psd":
                    sentence.append(_parse_node(node))
                elif _type == "deep":
                    sentence.append(_parse_node_psdx(node))
                inserted = True
    return corpus

def parse_deep_string(s):
    """This function creates a corpus from a string of PSDX-format trees separated
by single blank lines.

    :param str s: The string to process
    :returns: The corpus
    :rtype: :class:`lovett.corpus.corpus`

    """
    return parse_psd_string(s, _type="deep")

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
        once = False
        for s in m:
            i = _parse_meta_inner(s)
            if isinstance(i, (str)):
                if once:
                    raise PsdParseError("malformed metadata: %s" % str(node))
                once = True
                node.text = i
            else:
                node.append(i)
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

def _find(tag):
    return lambda t: t.node == tag

def _parse_node_psdx(node):
    if any(map(_find("ORTHO"), node)):
        return _parse_text_psdx(node)
    if any(map(_find("ALT-ORTHO"), node)):
        return _parse_empty_psdx(node)
    r = E.nonterminal()
    r.set_label(node.node)
    m = next(filter(_find("META"), node), None)
    if m is not None:
        r.append(_parse_metadata(m))
    for s in node:
        if s.node != "META":
            r.append(_parse_node_psdx(s))
    return r

def _parse_text_psdx(node):
    r = E.text()
    label, index,idxtype = _get_index_parts(node.node)
    r.set_label(label)
    t = next(filter(_find("ORTHO"), node), None)
    t = t[0]
    if t.startswith("$"):
        t = t[1:]
    if t.endswith("$"):
        t = t[:-1]
    r.text = t
    m = next(filter(_find("META"), node), None)
    if m is not None:
        r.append(_parse_metadata(m))
    if index is not None:
        md = r.metadata()
        md["index"] = index
        md["idxtype"] = idxtype
    return r

def _parse_empty_psdx(node):
    if node.node == "CODE":
        return _parse_comment_psdx(node)
    t = next(filter(_find("ALT-ORTHO"), node), None)[0]
    if t == "0":
        r = E.ec()
        r.set_ectype("zero")
    elif t == "*":
        r = E.ec()
        r.set_ectype("star")
    else:
        t = t.replace("*", "")
        tn, index, idxtype = _get_index_parts(t)
        if tn.isupper():
            r = E.trace()
            r.set_tracetype(tn)
            label = node.node
        elif tn.islower():
            r = E.ec()
            r.set_ectype(t)
        else:
            raise PsdParseError("Unknown empty node: %s" % node.node)
    if r.tag == "ec":
            label, index, idxtype = _get_index_parts(node.node)
    r.set_label(label)
    m = next(filter(_find("META"), node), None)
    if m is not None:
        r.append(_parse_metadata(m))
    if index is not None:
        md = r.metadata()
        md["index"] = index
        md["idxtype"] = idxtype
    return r

def _parse_comment_psdx(node):
    r = E.comment()
    typ, txt = node[0].split(":")
    # Slice off leading {
    r.set_comtype(typ[1:])
    # Slice off trailing }
    # TODO: not idempotent; underscores in XML go to spaces on round trip
    r.text = txt[:-1].replace("_", " ")

def _get_index_parts(s):
    l = s.split("=")
    if len(l) == 2:
        idxtype = "gap"
        index = l[1]
        label = l[0]
    else:
        l = l[0].split("-")
        if l[-1].isdigit():
            idxtype = "regular"
            index = l[-1]
            label = "-".join(l[:-1])
        else:
            label = s
            index = None
            idxtype = None
    return (label, index, idxtype)

class PsdParseError(Exception):
    """This class represents errors encoundered in the processing of PSD(X)
trees."""
    pass
