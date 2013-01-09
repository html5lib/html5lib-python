u"""Module for supporting the lxml.etree library. The idea here is to use as much
of the native library as possible, without using fragile hacks like custom element
names that break between releases. The downside of this is that we cannot represent
all possible trees; specifically the following are known to cause problems:

Text or comments as siblings of the root element
Docypes with no name

When any of these things occur, we emit a DataLossWarning
"""

from __future__ import absolute_import
import warnings
import re
import sys

from . import _base
from html5lib.constants import DataLossWarning
import html5lib.constants as constants
from . import etree as etree_builders
from html5lib import ihatexml

try:
    import lxml.etree as etree
except ImportError:
    pass

fullTree = True
tag_regexp = re.compile(u"{([^}]*)}(.*)")


class DocumentType(object):
    def __init__(self, name, publicId, systemId):
        self.name = name         
        self.publicId = publicId
        self.systemId = systemId
    __init__.func_annotations = {}

class Document(object):
    def __init__(self):
        self._elementTree = None
        self._childNodes = []
    __init__.func_annotations = {}

    def appendChild(self, element):
        self._elementTree.getroot().addnext(element._element)
    appendChild.func_annotations = {}

    def _getChildNodes(self):
        return self._childNodes
    _getChildNodes.func_annotations = {}
    
    childNodes = property(_getChildNodes)

def testSerializer(element):
    rv = []
    finalText = None
    infosetFilter = ihatexml.InfosetFilter()
    def serializeElement(element, indent=0):
        if not hasattr(element, u"tag"):
            if  hasattr(element, u"getroot"):
                #Full tree case
                rv.append(u"#document")
                if element.docinfo.internalDTD:
                    if not (element.docinfo.public_id or 
                            element.docinfo.system_url):
                        dtd_str = u"<!DOCTYPE %s>"%element.docinfo.root_name
                    else:
                        dtd_str = u"""<!DOCTYPE %s "%s" "%s">"""%(
                            element.docinfo.root_name, 
                            element.docinfo.public_id,
                            element.docinfo.system_url)
                    rv.append(u"|%s%s"%(u' '*(indent+2), dtd_str))
                next_element = element.getroot()
                while next_element.getprevious() is not None:
                    next_element = next_element.getprevious()
                while next_element is not None:
                    serializeElement(next_element, indent+2)
                    next_element = next_element.getnext()
            elif isinstance(element, unicode) or isinstance(element, str):
                #Text in a fragment
                assert isinstance(element, unicode) or sys.version_info.major == 2
                rv.append(u"|%s\"%s\""%(u' '*indent, element))
            else:
                #Fragment case
                rv.append(u"#document-fragment")
                for next_element in element:
                    serializeElement(next_element, indent+2)
        elif type(element.tag) == type(etree.Comment):
            rv.append(u"|%s<!-- %s -->"%(u' '*indent, element.text))
            if hasattr(element, u"tail") and element.tail:
                rv.append(u"|%s\"%s\"" %(u' '*indent, element.tail))
        else:
            assert isinstance(element, etree._Element)
            nsmatch = etree_builders.tag_regexp.match(element.tag)
            if nsmatch is not None:
                ns = nsmatch.group(1)
                tag = nsmatch.group(2)
                prefix = constants.prefixes[ns]
                rv.append(u"|%s<%s %s>"%(u' '*indent, prefix,
                                        infosetFilter.fromXmlName(tag)))
            else:
                rv.append(u"|%s<%s>"%(u' '*indent,
                                     infosetFilter.fromXmlName(element.tag)))

            if hasattr(element, u"attrib"):
                attributes = []
                for name, value in element.attrib.items():
                    nsmatch = tag_regexp.match(name)
                    if nsmatch is not None:
                        ns, name = nsmatch.groups()
                        name = infosetFilter.fromXmlName(name)
                        prefix = constants.prefixes[ns]
                        attr_string = u"%s %s"%(prefix, name)
                    else:
                        attr_string = infosetFilter.fromXmlName(name)
                    attributes.append((attr_string, value))

                for name, value in sorted(attributes):
                    rv.append(u'|%s%s="%s"' % (u' '*(indent+2), name, value))

            if element.text:
                rv.append(u"|%s\"%s\"" %(u' '*(indent+2), element.text))
            indent += 2
            for child in element.getchildren():
                serializeElement(child, indent)
            if hasattr(element, u"tail") and element.tail:
                rv.append(u"|%s\"%s\"" %(u' '*(indent-2), element.tail))
    serializeElement.func_annotations = {}
    serializeElement(element, 0)

    if finalText is not None:
        rv.append(u"|%s\"%s\""%(u' '*2, finalText))

    return u"\n".join(rv)
testSerializer.func_annotations = {}

def tostring(element):
    u"""Serialize an element and its child nodes to a string"""
    rv = []
    finalText = None
    def serializeElement(element):
        if not hasattr(element, u"tag"):
            if element.docinfo.internalDTD:
                if element.docinfo.doctype:
                    dtd_str = element.docinfo.doctype
                else:
                    dtd_str = u"<!DOCTYPE %s>"%element.docinfo.root_name
                rv.append(dtd_str)
            serializeElement(element.getroot())
            
        elif type(element.tag) == type(etree.Comment):
            rv.append(u"<!--%s-->"%(element.text,))
        
        else:
            #This is assumed to be an ordinary element
            if not element.attrib:
                rv.append(u"<%s>"%(element.tag,))
            else:
                attr = u" ".join([u"%s=\"%s\""%(name, value) 
                                 for name, value in element.attrib.items()])
                rv.append(u"<%s %s>"%(element.tag, attr))
            if element.text:
                rv.append(element.text)

            for child in element.getchildren():
                serializeElement(child)

            rv.append(u"</%s>"%(element.tag,))

        if hasattr(element, u"tail") and element.tail:
            rv.append(element.tail)
    serializeElement.func_annotations = {}

    serializeElement(element)

    if finalText is not None:
        rv.append(u"%s\""%(u' '*2, finalText))

    return u"".join(rv)
tostring.func_annotations = {}
        

class TreeBuilder(_base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = None
    commentClass = None
    fragmentClass = Document    

    def __init__(self, namespaceHTMLElements, fullTree = False):
        builder = etree_builders.getETreeModule(etree, fullTree=fullTree)
        infosetFilter = self.infosetFilter = ihatexml.InfosetFilter()
        self.namespaceHTMLElements = namespaceHTMLElements

        class Attributes(dict):
            def __init__(self, element, value={}):
                self._element = element
                dict.__init__(self, value)
                for key, value in self.items():
                    if isinstance(key, tuple):
                        name = u"{%s}%s"%(key[2], infosetFilter.coerceAttribute(key[1]))
                    else:
                        name = infosetFilter.coerceAttribute(key)
                    self._element._element.attrib[name] = value
            __init__.func_annotations = {}

            def __setitem__(self, key, value):
                dict.__setitem__(self, key, value)
                if isinstance(key, tuple):
                    name = u"{%s}%s"%(key[2], infosetFilter.coerceAttribute(key[1]))
                else:
                    name = infosetFilter.coerceAttribute(key)
                self._element._element.attrib[name] = value
            __setitem__.func_annotations = {}

        class Element(builder.Element):
            def __init__(self, name, namespace):
                name = infosetFilter.coerceElement(name)
                builder.Element.__init__(self, name, namespace=namespace)
                self._attributes = Attributes(self)
            __init__.func_annotations = {}

            def _setName(self, name):
                self._name = infosetFilter.coerceElement(name)
                self._element.tag = self._getETreeTag(
                    self._name, self._namespace)
            _setName.func_annotations = {}
        
            def _getName(self):
                return infosetFilter.fromXmlName(self._name)
            _getName.func_annotations = {}
        
            name = property(_getName, _setName)

            def _getAttributes(self):
                return self._attributes
            _getAttributes.func_annotations = {}

            def _setAttributes(self, attributes):
                self._attributes = Attributes(self, attributes)
            _setAttributes.func_annotations = {}
    
            attributes = property(_getAttributes, _setAttributes)

            def insertText(self, data, insertBefore=None):
                data = infosetFilter.coerceCharacters(data)
                builder.Element.insertText(self, data, insertBefore)
            insertText.func_annotations = {}

            def appendChild(self, child):
                builder.Element.appendChild(self, child)
            appendChild.func_annotations = {}
                

        class Comment(builder.Comment):
            def __init__(self, data):
                data = infosetFilter.coerceComment(data)
                builder.Comment.__init__(self, data)
            __init__.func_annotations = {}

            def _setData(self, data):
                data = infosetFilter.coerceComment(data)
                self._element.text = data
            _setData.func_annotations = {}

            def _getData(self):
                return self._element.text
            _getData.func_annotations = {}

            data = property(_getData, _setData)

        self.elementClass = Element
        self.commentClass = builder.Comment
        #self.fragmentClass = builder.DocumentFragment
        _base.TreeBuilder.__init__(self, namespaceHTMLElements)
    __init__.func_annotations = {}
    
    def reset(self):
        _base.TreeBuilder.reset(self)
        self.insertComment = self.insertCommentInitial
        self.initial_comments = []
        self.doctype = None
    reset.func_annotations = {}

    def testSerializer(self, element):
        return testSerializer(element)
    testSerializer.func_annotations = {}

    def getDocument(self):
        if fullTree:
            return self.document._elementTree
        else:
            return self.document._elementTree.getroot()
    getDocument.func_annotations = {}
    
    def getFragment(self):
        fragment = []
        element = self.openElements[0]._element
        if element.text:
            fragment.append(element.text)
        fragment.extend(element.getchildren())
        if element.tail:
            fragment.append(element.tail)
        return fragment
    getFragment.func_annotations = {}

    def insertDoctype(self, token):
        name = token[u"name"]
        publicId = token[u"publicId"]
        systemId = token[u"systemId"]

        if not name or ihatexml.nonXmlNameBMPRegexp.search(name) or name[0] == u'"':
            warnings.warn(u"lxml cannot represent null or non-xml doctype", DataLossWarning)

        doctype = self.doctypeClass(name, publicId, systemId)
        self.doctype = doctype
    insertDoctype.func_annotations = {}
    
    def insertCommentInitial(self, data, parent=None):
        self.initial_comments.append(data)
    insertCommentInitial.func_annotations = {}

    def insertCommentMain(self, data, parent=None):
        if (parent == self.document and
            type(self.document._elementTree.getroot()[-1].tag) == type(etree.Comment)):
                warnings.warn(u"lxml cannot represent adjacent comments beyond the root elements", DataLossWarning)
        super(TreeBuilder, self).insertComment(data, parent)
    insertCommentMain.func_annotations = {}
    
    def insertRoot(self, token):
        u"""Create the document root"""
        #Because of the way libxml2 works, it doesn't seem to be possible to
        #alter information like the doctype after the tree has been parsed. 
        #Therefore we need to use the built-in parser to create our iniial 
        #tree, after which we can add elements like normal
        docStr = u""
        if self.doctype and self.doctype.name and not self.doctype.name.startswith(u'"'):
            docStr += u"<!DOCTYPE %s"%self.doctype.name
            if (self.doctype.publicId is not None or 
                self.doctype.systemId is not None):
                docStr += u' PUBLIC "%s" "%s"'%(self.doctype.publicId or u"",
                                               self.doctype.systemId or u"")
            docStr += u">"
            if self.doctype.name != token[u"name"]:
                warnings.warn(u"lxml cannot represent doctype with a different name to the root element", DataLossWarning)
        docStr += u"<THIS_SHOULD_NEVER_APPEAR_PUBLICLY/>"
        
        try:
            root = etree.fromstring(docStr)
        except etree.XMLSyntaxError:
            print docStr
            raise
        
        #Append the initial comments:
        for comment_token in self.initial_comments:
            root.addprevious(etree.Comment(comment_token[u"data"]))
        
        #Create the root document and add the ElementTree to it
        self.document = self.documentClass()
        self.document._elementTree = root.getroottree()
        
        # Give the root element the right name
        name = token[u"name"]
        namespace = token.get(u"namespace", self.defaultNamespace)
        if namespace is None:
            etree_tag = name
        else:
            etree_tag = u"{%s}%s"%(namespace, name)
        root.tag = etree_tag
        
        #Add the root element to the internal child/open data structures
        root_element = self.elementClass(name, namespace)
        root_element._element = root
        self.document._childNodes.append(root_element)
        self.openElements.append(root_element)
    
        #Reset to the default insert comment function
        self.insertComment = self.insertCommentMain
    insertRoot.func_annotations = {}
