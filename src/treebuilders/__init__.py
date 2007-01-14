"""A collection of modules for building different kinds of tree from
HTML documents.

To create a treebuilder for a new type of tree, you need to do
implement several things:

1) A set of classes for various types of elements: Document, Doctype,
Comment, Element. These must implement the interface of
_base.treebuilders.Node (although comment nodes have a different
signature for their constructor, see treebuilders.simpletree.Comment)
Textual content may also be implemented as another node type, or not, as
your tree implementation requires.

2) A treebuilder object (called TreeBuilder by convention) that
inherits from treebuilders._base.TreeBuilder. This has 4 required attributes:
documentClass - the class to use for the bottommost node of a document
elementClass - the class to use for HTML Elements
commentClass - the class to use for comments
doctypeClass - the class to use for doctypes
It also has one required method:
getDocument - Returns the root node of the complete document tree

3) If you wish to run the unit tests, you must also create a
testSerializer method on your treebuilder which accepts a node and
returns a string containing Node and its children serialized according
to the format used in the unittests

The supplied simpletree module provides a python-only implementation
of a full treebuilder and is a useful reference for the semantics of
the various methods.
"""

import os.path
__path__.append(os.path.dirname(__path__[0]))

import dom
import simpletree

try:
    import etree
except:
    pass
