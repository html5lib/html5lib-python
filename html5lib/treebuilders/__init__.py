# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""A collection of modules for building different kinds of tree from
HTML documents.

To create a treebuilder for a new type of tree, you need to do
implement several things:

1) A set of classes for various types of elements: Document, Doctype,
Comment, Element. These must implement the interface of
_base.treebuilders.Node (although comment nodes have a different
signature for their constructor, see treebuilders.etree.Comment)
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
"""

from __future__ import absolute_import, division, unicode_literals

from .._utils import default_etree

treeBuilderCache = {}


def getTreeBuilder(treeType, implementation=None, **kwargs):
    """Get a TreeBuilder class for various types of tree with built-in support

    treeType - the name of the tree type required (case-insensitive). Supported
               values are:

               "dom" - A generic builder for DOM implementations, defaulting to
                       a xml.dom.minidom based implementation.
               "etree" - A generic builder for tree implementations exposing an
                         ElementTree-like interface, defaulting to
                         xml.etree.cElementTree if available and
                         xml.etree.ElementTree if not.
               "lxml" - A etree-based builder for lxml.etree, handling
                        limitations of lxml's implementation.

    implementation - (Currently applies to the "etree" and "dom" tree types). A
                      module implementing the tree type e.g.
                      xml.etree.ElementTree or xml.etree.cElementTree."""

    treeType = treeType.lower()
    if treeType not in treeBuilderCache:
        if treeType == "dom":
            from . import dom
            # Come up with a sane default (pref. from the stdlib)
            if implementation is None:
                from xml.dom import minidom
                implementation = minidom
            # NEVER cache here, caching is done in the dom submodule
            return dom.getDomModule(implementation, **kwargs).TreeBuilder
        elif treeType == "lxml":
            from . import etree_lxml
            treeBuilderCache[treeType] = etree_lxml.TreeBuilder
        elif treeType == "etree":
            from . import etree
            if implementation is None:
                implementation = default_etree
            # NEVER cache here, caching is done in the etree submodule
            return etree.getETreeModule(implementation, **kwargs).TreeBuilder
        else:
            raise ValueError("""Unrecognised treebuilder "%s" """ % treeType)
    return treeBuilderCache.get(treeType)
