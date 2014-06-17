PSD XML format
==============

This document describes an XML format for representing parsed corpus
files.  The extension for files in this format is ``psdx``.  This format
is designed to make possible the representation of trees in the Penn
Historical Corpora format (designated with the abbreviation PSD, based
on the preferred file extension) (TODO: link).  The format is a (near)
superset of the PSD format; Lovett provides facilities to interconvert
between the PSD and PSDX formats.  The PSDX format is capable of
representing other sets of annotation conventions.  Nonetheless, it
relies on several basic tenets of the Penn tradition, such as the
division of the corpus into sentences and the non-imposition of any
template (such as X-bar) on the sentences in the corpus.

Conventions
-----------

The following are miscellaneous conventions governing the implementation
of the format:

* Tag names are not case-sensitive, but are canonically lowercase.
* It is good practice to escape any non-ASCII characters in the text
  with XML character references (TODO: link), or to encode the PSDX file
  in UTF8.
* Whitespace is not significant

::

    TODO: other discussions:
    - why not standoff annotation?

Tags
----

This section describes the XML tags that compose the format.

Corpus
^^^^^^

The root element of the file should be a ``corpus`` node.  This node has
no legal attributes.  The daughters of the ``corpus`` node are
``sentence`` elements.

::
    <corpus>
      sentence-1
      sentence-2
      ...
      sentence-n
    </corpus>

Sentence
^^^^^^^^

Each sentence of the corpus is contained in a ``sentence`` tag.   The
following (only) are legitimate attributes of this tag, all of which are
optional:

``id``
    A (globally) unique identifier string for the sentence

The sentence has a single daughter, which is a ``nonterminal``, ``text``,
or ``comment`` tag.

::
    <sentence id="foo">
      <daughter>
        ...
      </daughter>
    </sentence>

Nonterminal
^^^^^^^^^^^

Nonterminal nodes in the parse tree are represented by a ``nonterminal``
tag.  This tag has one mandatory attribute:

``category``
    The category of this non-terminal (NP, IP, etc.)  This corresponds
    to the label of the node in the PSD format up to (not including) the
    first dash.

The tag also has one optional attribute:

``subcategory``
    A subtype of the node’s category to which it belongs.  This
    corresponds to the first dash tag (only) in the PSD format.  For
    example, the PPCEME (TODO: link) has (non-exhaustively) the
    following subcategories for NPs:
    ``SBJ``
        subject
    ``OB1``
        direct object
    ``OB2``
        indirect object
    ``PRD``
        predicate nominal

Categories can fall into one of two classes:

punctuation
    A punctuation category is one of the chacracters ``.`` or ``,``
    (period and comma)
nonmunctuation
    A nonpunctuation category must start with an uppercase letter of the
    English alphabet.  Subsequent characters may be uppercase English
    letters or Arabic numerals 0–9.

Subcategories may only be nonpunctuation.

Nonterminal nodes must not be empty; they may contain other nonterminals
and/or any of the terminal types discussed below.

Here is an example:

::
    <nonterminal category="NP" subcategory="SBJ">
      ...
    </nonterminal>


Terminal node types
^^^^^^^^^^^^^^^^^^^

In this section, types of terminal nodes are described.

Text
""""

Text ``text`` represent written (or spoken) material present in the source
text.  They have obligatory ``category`` and optional ``subcategory``
attributes as described above for nonterminals.  They have no other licit
attributes.  They must contain exactly one non-whitespace XML text node.
Here is an example:

::
    <text category="N">
      foo
    </text>

Trace
"""""

A ``trace`` node represents the trace of movement.  It has obligatory
``category`` and optional ``subcategory`` attributes as described
above for nonterminals.  In the PSD format, these are represented by
an asterisk, one or more uppercase letters, and another asterisk.
They come in several varieties:

``*T*``
    *wh* traces
``*ICH*``
    traces of extraposition (“interpret constituent here”)
``*CL*``
    traces of clitics

Trace nodes have the following mandatory attribute:
``tracetype``
    The kind of trace: “T”, “ICH”, or “CL” (or another type).  Trace
    types must consist only of one or more uppercase English letters

Additionally, traces must have an index specified in their metadata.
For an example of a trace, consult the example annotated sentence
below.

Empty category
""""""""""""""

An ``ec`` node represents an empty category – that is, a syntactic hole
not related to a movement operation.  Just as with ``trace`` and
``text``, ``ec`` nodes have ``category`` and ``subcategory``
attributes.  There are several varieties of empty categories in the
Penn-style parsed historical corpora:
``0``
    Phonologically null elements of various syntactic categories, such
    as the complementizer in the sentence “John said ___ he was sick last
    week.”
``*``
    An empty (elided) verb, as in TODO: example
``*pro*``
    A pro-dropped subject
``*exp*``
    An empty expletive subject
``*arb*``
    An empty arbitrary subject

An empty category node has the following mandatory attribute:
``ectype``
    The kind of empty category.  Can be “zero” for a ``0``, “star” for a
    ``*``, or any other string of lowercase English letters.

This node type has no other possible attributes.

TODO: example

Comment
"""""""

A ``comment`` node represents a comment which is embedded in the corpus
annotation.  A comment could (for example) explain the rationale behind
the annotation of an uncommon or aberrant structure, or be inserted as a
flag to remind annotators to revise a preliminary parse.  XML comments
(delimited by ``<!-- ... -->``) are not used to represent annotation
comments because the former are not handled uniformly by XML parsing
libraries.

In principle, comments in the PSD format are nodes with the category
``CODE``.  It is recommended that they have a structured format where
the text is surrounded by braces, and the comment type precedes the
actual text:

::
    (CODE {TODO:revise_this_sentence})

However, in some released corpora this convention is not followed, such
as for example the PPCEME.  Instead, bare comments are used (for
example, to encode formatting tags present in the source text):

::
    (CODE <font>)

PSDX ``comment`` elements have a mandatory attribute, which is the only
attribute they may have:

``comtype``
    The type of comment this is.  This corresponds to the letters before
    the colon in the structured format (“TODO” in the example above).
    It may consist only of uppercase English letters.

Bare comments in the PSD format are converted to the generic “COM” type.
Bare comments are never emitted by Lovett’s converter.  (This is one way
in which the two conversion processes are not exact inverses of each
other.)

Metadata
^^^^^^^^
