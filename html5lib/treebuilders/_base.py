from __future__ import absolute_import
from html5lib.constants import scopingElements, tableInsertModeElements, namespaces
try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

# The scope markers are inserted when entering object elements,
# marquees, table cells, and table captions, and are used to prevent formatting
# from "leaking" into tables, object elements, and marquees.
Marker = None

listElementsMap = {
    None:(frozenset(scopingElements), False),
    u"button":(frozenset(scopingElements | set([(namespaces[u"html"], u"button")])), False),
    u"list":(frozenset(scopingElements | set([(namespaces[u"html"], u"ol"),
                                   (namespaces[u"html"], u"ul")])), False),
    u"table":(frozenset([(namespaces[u"html"], u"html"),
                  (namespaces[u"html"], u"table")]), False),
    u"select":(frozenset([(namespaces[u"html"], u"optgroup"), 
                   (namespaces[u"html"], u"option")]), True)
    }


class Node(object):
    def __init__(self, name):
        u"""Node representing an item in the tree.
        name - The tag name associated with the node
        parent - The parent of the current node (or None for the document node)
        value - The value of the current node (applies to text nodes and 
        comments
        attributes - a dict holding name, value pairs for attributes of the node
        childNodes - a list of child nodes of the current node. This must 
        include all elements but not necessarily other node types
        _flags - A list of miscellaneous flags that can be set on the node
        """
        self.name = name
        self.parent = None
        self.value = None
        self.attributes = {}
        self.childNodes = []
        self._flags = []
    __init__.func_annotations = {}

    def __unicode__(self):
        attributesStr =  u" ".join([u"%s=\"%s\""%(name, value) 
                                   for name, value in 
                                   self.attributes.items()])
        if attributesStr:
            return u"<%s %s>"%(self.name,attributesStr)
        else:
            return u"<%s>"%(self.name)
    __unicode__.func_annotations = {}

    def __repr__(self):
        return u"<%s>" % (self.name)
    __repr__.func_annotations = {}

    def appendChild(self, node):
        u"""Insert node as a child of the current node
        """
        raise NotImplementedError
    appendChild.func_annotations = {}

    def insertText(self, data, insertBefore=None):
        u"""Insert data as text in the current node, positioned before the 
        start of node insertBefore or to the end of the node's text.
        """
        raise NotImplementedError
    insertText.func_annotations = {}

    def insertBefore(self, node, refNode):
        u"""Insert node as a child of the current node, before refNode in the 
        list of child nodes. Raises ValueError if refNode is not a child of 
        the current node"""
        raise NotImplementedError
    insertBefore.func_annotations = {}

    def removeChild(self, node):
        u"""Remove node from the children of the current node
        """
        raise NotImplementedError
    removeChild.func_annotations = {}

    def reparentChildren(self, newParent):
        u"""Move all the children of the current node to newParent. 
        This is needed so that trees that don't store text as nodes move the 
        text in the correct way
        """
        #XXX - should this method be made more general?
        for child in self.childNodes:
            newParent.appendChild(child)
        self.childNodes = []
    reparentChildren.func_annotations = {}

    def cloneNode(self):
        u"""Return a shallow copy of the current node i.e. a node with the same
        name and attributes but with no parent or child nodes
        """
        raise NotImplementedError
    cloneNode.func_annotations = {}


    def hasContent(self):
        u"""Return true if the node has children or text, false otherwise
        """
        raise NotImplementedError
    hasContent.func_annotations = {}

class ActiveFormattingElements(list):
    def append(self, node):
        equalCount = 0
        if node != Marker:
            for element in self[::-1]:
                if element == Marker:
                    break
                if self.nodesEqual(element, node):
                    equalCount += 1
                if equalCount == 3:
                    self.remove(element)
                    break
        list.append(self, node)
    append.func_annotations = {}

    def nodesEqual(self, node1, node2):
        if not node1.nameTuple == node2.nameTuple:
            return False
        
        if not node1.attributes == node2.attributes:
            return False
        
        return True
    nodesEqual.func_annotations = {}

class TreeBuilder(object):
    u"""Base treebuilder implementation
    documentClass - the class to use for the bottommost node of a document
    elementClass - the class to use for HTML Elements
    commentClass - the class to use for comments
    doctypeClass - the class to use for doctypes
    """

    #Document class
    documentClass = None

    #The class to use for creating a node
    elementClass = None

    #The class to use for creating comments
    commentClass = None

    #The class to use for creating doctypes
    doctypeClass = None
    
    #Fragment class
    fragmentClass = None

    def __init__(self, namespaceHTMLElements):
        if namespaceHTMLElements:
            self.defaultNamespace = u"http://www.w3.org/1999/xhtml"
        else:
            self.defaultNamespace = None
        self.reset()
    __init__.func_annotations = {}
    
    def reset(self):
        self.openElements = []
        self.activeFormattingElements = ActiveFormattingElements()

        #XXX - rename these to headElement, formElement
        self.headPointer = None
        self.formPointer = None

        self.insertFromTable = False

        self.document = self.documentClass()
    reset.func_annotations = {}

    def elementInScope(self, target, variant=None):

        #If we pass a node in we match that. if we pass a string
        #match any node with that name
        exactNode = hasattr(target, u"nameTuple")

        listElements, invert = listElementsMap[variant]

        for node in reversed(self.openElements):
            if (node.name == target and not exactNode or
                node == target and exactNode):
                return True
            elif (invert ^ (node.nameTuple in listElements)):                
                return False

        assert False # We should never reach this point
    elementInScope.func_annotations = {}

    def reconstructActiveFormattingElements(self):
        # Within this algorithm the order of steps described in the
        # specification is not quite the same as the order of steps in the
        # code. It should still do the same though.

        # Step 1: stop the algorithm when there's nothing to do.
        if not self.activeFormattingElements:
            return

        # Step 2 and step 3: we start with the last element. So i is -1.
        i = len(self.activeFormattingElements) - 1
        entry = self.activeFormattingElements[i]
        if entry == Marker or entry in self.openElements:
            return

        # Step 6
        while entry != Marker and entry not in self.openElements:
            if i == 0:
                #This will be reset to 0 below
                i = -1
                break
            i -= 1
            # Step 5: let entry be one earlier in the list.
            entry = self.activeFormattingElements[i]

        while True:
            # Step 7
            i += 1

            # Step 8
            entry = self.activeFormattingElements[i]
            clone = entry.cloneNode() #Mainly to get a new copy of the attributes

            # Step 9
            element = self.insertElement({u"type":u"StartTag", 
                                          u"name":clone.name, 
                                          u"namespace":clone.namespace, 
                                          u"data":clone.attributes})

            # Step 10
            self.activeFormattingElements[i] = element

            # Step 11
            if element == self.activeFormattingElements[-1]:
                break
    reconstructActiveFormattingElements.func_annotations = {}

    def clearActiveFormattingElements(self):
        entry = self.activeFormattingElements.pop()
        while self.activeFormattingElements and entry != Marker:
            entry = self.activeFormattingElements.pop()
    clearActiveFormattingElements.func_annotations = {}

    def elementInActiveFormattingElements(self, name):
        u"""Check if an element exists between the end of the active
        formatting elements and the last marker. If it does, return it, else
        return false"""

        for item in self.activeFormattingElements[::-1]:
            # Check for Marker first because if it's a Marker it doesn't have a
            # name attribute.
            if item == Marker:
                break
            elif item.name == name:
                return item
        return False
    elementInActiveFormattingElements.func_annotations = {}

    def insertRoot(self, token):
        element = self.createElement(token)
        self.openElements.append(element)
        self.document.appendChild(element)
    insertRoot.func_annotations = {}

    def insertDoctype(self, token):
        name = token[u"name"]
        publicId = token[u"publicId"]
        systemId = token[u"systemId"]

        doctype = self.doctypeClass(name, publicId, systemId)
        self.document.appendChild(doctype)
    insertDoctype.func_annotations = {}

    def insertComment(self, token, parent=None):
        if parent is None:
            parent = self.openElements[-1]
        parent.appendChild(self.commentClass(token[u"data"]))
    insertComment.func_annotations = {}
                           
    def createElement(self, token):
        u"""Create an element but don't insert it anywhere"""
        name = token[u"name"]
        namespace = token.get(u"namespace", self.defaultNamespace)
        element = self.elementClass(name, namespace)
        element.attributes = token[u"data"]
        return element
    createElement.func_annotations = {}

    def _getInsertFromTable(self):
        return self._insertFromTable
    _getInsertFromTable.func_annotations = {}

    def _setInsertFromTable(self, value):
        u"""Switch the function used to insert an element from the
        normal one to the misnested table one and back again"""
        self._insertFromTable = value
        if value:
            self.insertElement = self.insertElementTable
        else:
            self.insertElement = self.insertElementNormal
    _setInsertFromTable.func_annotations = {}

    insertFromTable = property(_getInsertFromTable, _setInsertFromTable)
        
    def insertElementNormal(self, token):
        name = token[u"name"]
        assert type(name) == unicode, u"Element %s not unicode"%name
        namespace = token.get(u"namespace", self.defaultNamespace)
        element = self.elementClass(name, namespace)
        element.attributes = token[u"data"]
        self.openElements[-1].appendChild(element)
        self.openElements.append(element)
        return element
    insertElementNormal.func_annotations = {}

    def insertElementTable(self, token):
        u"""Create an element and insert it into the tree""" 
        element = self.createElement(token)
        if self.openElements[-1].name not in tableInsertModeElements:
            return self.insertElementNormal(token)
        else:
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            parent, insertBefore = self.getTableMisnestedNodePosition()
            if insertBefore is None:
                parent.appendChild(element)
            else:
                parent.insertBefore(element, insertBefore)
            self.openElements.append(element)
        return element
    insertElementTable.func_annotations = {}

    def insertText(self, data, parent=None):
        u"""Insert text data."""
        if parent is None:
            parent = self.openElements[-1]

        if (not self.insertFromTable or (self.insertFromTable and
                                         self.openElements[-1].name 
                                         not in tableInsertModeElements)):
            parent.insertText(data)
        else:
            # We should be in the InTable mode. This means we want to do
            # special magic element rearranging
            parent, insertBefore = self.getTableMisnestedNodePosition()
            parent.insertText(data, insertBefore)
    insertText.func_annotations = {}
            
    def getTableMisnestedNodePosition(self):
        u"""Get the foster parent element, and sibling to insert before
        (or None) when inserting a misnested table node"""
        # The foster parent element is the one which comes before the most
        # recently opened table element
        # XXX - this is really inelegant
        lastTable=None
        fosterParent = None
        insertBefore = None
        for elm in self.openElements[::-1]:
            if elm.name == u"table":
                lastTable = elm
                break
        if lastTable:
            # XXX - we should really check that this parent is actually a
            # node here
            if lastTable.parent:
                fosterParent = lastTable.parent
                insertBefore = lastTable
            else:
                fosterParent = self.openElements[
                    self.openElements.index(lastTable) - 1]
        else:
            fosterParent = self.openElements[0]
        return fosterParent, insertBefore
    getTableMisnestedNodePosition.func_annotations = {}

    def generateImpliedEndTags(self, exclude=None):
        name = self.openElements[-1].name
        # XXX td, th and tr are not actually needed
        if (name in frozenset((u"dd", u"dt", u"li", u"option", u"optgroup", u"p", u"rp", u"rt"))
            and name != exclude):
            self.openElements.pop()
            # XXX This is not entirely what the specification says. We should
            # investigate it more closely.
            self.generateImpliedEndTags(exclude)
    generateImpliedEndTags.func_annotations = {}

    def getDocument(self):
        u"Return the final tree"
        return self.document
    getDocument.func_annotations = {}
    
    def getFragment(self):
        u"Return the final fragment"
        #assert self.innerHTML
        fragment = self.fragmentClass()
        self.openElements[0].reparentChildren(fragment)
        return fragment
    getFragment.func_annotations = {}

    def testSerializer(self, node):
        u"""Serialize the subtree of node in the format required by unit tests
        node - the node from which to start serializing"""
        raise NotImplementedError
    testSerializer.func_annotations = {}
