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

treeBuilderCache = {}

def getTreeBuilder(treeType, implementation=None, **kwargs):
    """Get a TreeBuilder class for various types of tree with built-in support
    
    treeType - the name of the tree type required (case-insensitive). Supported
               values are "simpletree", "dom", "etree" and "beautifulsoup"
               
               "simpletree" - a built-in DOM-ish tree type with support for some
                              more pythonic idioms.
                "dom" - The xml.dom.minidom DOM implementation
                "etree" - A generic builder for tree implementations exposing an
                          elementtree-like interface (known to work with
                          ElementTree, cElementTree and lxml.etree).
                "beautifulsoup" - Beautiful soup (if installed)
               
    implementation - (Currently applies to the "etree" tree type only). A module
                      implementing the tree type e.g. xml.etree.ElementTree or
                      lxml.etree."""
    
    treeType = treeType.lower()
    if treeType not in treeBuilderCache:
        if treeType in ("dom", "simpletree"):
            mod = __import__(treeType, globals())
            treeBuilderCache[treeType] = mod.TreeBuilder
        elif treeType == "beautifulsoup":
            import soup
            treeBuilderCache[treeType] = soup.TreeBuilder
        elif treeType == "etree":
            import etree
            # XXX: NEVER cache here, caching is done in the etree submodule
            return etree.getETreeModule(implementation, **kwargs).TreeBuilder
    return treeBuilderCache.get(treeType)
