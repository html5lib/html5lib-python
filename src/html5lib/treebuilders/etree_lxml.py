import _base
import new
import warnings
from html5lib.constants import DataLossWarning
import etree as etree_builders
from html5lib import ihatexml

try:
    import lxml.etree as etree
except ImportError:
    pass

fullTree = True

"""Module for supporting the lxml.etree library. The idea here is to use as much
of the native library as possible, without using fragile hacks like custom element
names that break between releases. The downside of this is that we cannot represent
all possible trees; specifically the following are known to cause problems:

Text or comments as siblings of the root element
Docypes with no name

When any of these things occur, we emit a DataLossWarning
"""

class DocumentType(object):
    def __init__(self, name, publicId, systemId):
        self.name = name
        if name != name.lower():
            warnings.warn("lxml does not preserve doctype case", DataLossWarning)           
        self.publicId = publicId
        self.systemId = systemId

class Document(object):
    def __init__(self):
        self._elementTree = None
        self._childNodes = []

    def appendChild(self, element):
        self._elementTree.getroot().addnext(element._element)

    def _getChildNodes(self):
        return self._childNodes
    
    childNodes = property(_getChildNodes)

def testSerializer(element):
    rv = []
    finalText = None
    filter = ihatexml.InfosetFilter()
    def serializeElement(element, indent=0):
        if not hasattr(element, "tag"):
            if  hasattr(element, "getroot"):
                #Full tree case
                rv.append("#document")
                if element.docinfo.internalDTD:
                    if not (element.docinfo.public_id or 
                            element.docinfo.system_url):
                        dtd_str = "<!DOCTYPE %s>"%element.docinfo.root_name
                    else:
                        dtd_str = """<!DOCTYPE %s "%s" "%s">"""%(
                            element.docinfo.root_name, 
                            element.docinfo.public_id,
                            element.docinfo.system_url)
                    rv.append("|%s%s"%(' '*(indent+2), dtd_str))
                next_element = element.getroot()
                while next_element.getprevious() is not None:
                    next_element = next_element.getprevious()
                while next_element is not None:
                    serializeElement(next_element, indent+2)
                    next_element = next_element.getnext()
            elif isinstance(element, basestring):
                #Text in a fragment
                rv.append("|%s\"%s\""%(' '*indent, element))
            else:
                #Fragment case
                rv.append("#document-fragment")
                for next_element in element:
                    serializeElement(next_element, indent+2)
        elif type(element.tag) == type(etree.Comment):
            rv.append("|%s<!-- %s -->"%(' '*indent, element.text))
        else:
            rv.append("|%s<%s>"%(' '*indent, filter.fromXmlName(element.tag)))
            if hasattr(element, "attrib"):
                for name, value in element.attrib.iteritems():
                    rv.append('|%s%s="%s"' % (' '*(indent+2), 
                                              filter.fromXmlName(name), value))
            if element.text:
                rv.append("|%s\"%s\"" %(' '*(indent+2), element.text))
            indent += 2
            for child in element.getchildren():
                serializeElement(child, indent)
        if hasattr(element, "tail") and element.tail:
            rv.append("|%s\"%s\"" %(' '*(indent-2), element.tail))
    serializeElement(element, 0)

    if finalText is not None:
        rv.append("|%s\"%s\""%(' '*2, finalText))

    return "\n".join(rv)

def tostring(element):
    """Serialize an element and its child nodes to a string"""
    rv = []
    finalText = None
    def serializeElement(element):
        if not hasattr(element, "tag"):
            if element.docinfo.internalDTD:
                if element.docinfo.doctype:
                    dtd_str = element.docinfo.doctype
                else:
                    dtd_str = "<!DOCTYPE %s>"%element.docinfo.root_name
                rv.append(dtd_str)
            serializeElement(element.getroot())
            
        elif type(element.tag) == type(etree.Comment):
            rv.append("<!--%s-->"%(element.text,))
        
        else:
            #This is assumed to be an ordinary element
            if not element.attrib:
                rv.append("<%s>"%(element.tag,))
            else:
                attr = " ".join(["%s=\"%s\""%(name, value) 
                                 for name, value in element.attrib.iteritems()])
                rv.append("<%s %s>"%(element.tag, attr))
            if element.text:
                rv.append(element.text)

            for child in element.getchildren():
                serializeElement(child)

            rv.append("</%s>"%(element.tag,))

        if hasattr(element, "tail") and element.tail:
            rv.append(element.tail)

    serializeElement(element)

    if finalText is not None:
        rv.append("%s\""%(' '*2, finalText))

    return "".join(rv)
        

class TreeBuilder(_base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = None
    commentClass = None
    fragmentClass = Document    

    def __init__(self, fullTree = False):
        builder = etree_builders.getETreeModule(etree, fullTree=fullTree)
        filter = self.filter = ihatexml.InfosetFilter()

        class Attributes(dict):
            def __init__(self, element, value={}):
                self._element = element
                dict.__init__(self, value)
                for k, v in self.iteritems():
                    self._element._element.attrib[filter.coerceAttribute(k)] = v

            def __setitem__(self, key, value):
                dict.__setitem__(self, key, value)
                self._element._element.attrib[filter.coerceAttribute(key)] = value

        class Element(builder.Element):
            def __init__(self, name):
                self._name = name
                builder.Element.__init__(self, filter.coerceElement(name))
                self._attributes = Attributes(self)

            def _setName(self, name):
                self._name = name
                self._element.tag = filter.coerceElement(name)

            def _getName(self):
                return self._name

            name = property(_getName, _setName)

            def _getAttributes(self):
                return self._attributes

            def _setAttributes(self, attributes):
                self._attributes = Attributes(self, attributes)
    
            attributes = property(_getAttributes, _setAttributes)

            def insertText(self, data, insertBefore=None):
                data = filter.coerceCharacters(data)
                builder.Element.insertText(self, data, insertBefore)

            def appendChild(self, child):
                builder.Element.appendChild(self, child)
                

        class Comment(builder.Comment):
            def __init__(self, data):
                data = filter.coerceComment(data)
                builder.Comment.__init__(self, data)

            def _setData(self, data):
                data = filter.coerceComment(data)
                self._element.text = data

            def _getData(self):
                return self._element.text

            data = property(_getData, _setData)

        self.elementClass = Element
        self.commentClass = builder.Comment
        #self.fragmentClass = builder.DocumentFragment
        _base.TreeBuilder.__init__(self)
    
    def reset(self):
        _base.TreeBuilder.reset(self)
        self.insertComment = self.insertCommentInitial
        self.initial_comments = []
        self.doctype = None

    def testSerializer(self, element):
        return testSerializer(element)

    def getDocument(self):
        if fullTree:
            return self.document._elementTree
        else:
            return self.document._elementTree.getroot()
    
    def getFragment(self):
        fragment = []
        element = self.openElements[0]._element
        if element.text:
            fragment.append(element.text)
        fragment.extend(element.getchildren())
        if element.tail:
            fragment.append(element.tail)
        return fragment

    def insertDoctype(self, name, publicId, systemId):
        if not name or ihatexml.nonXmlBMPRegexp.search(name):
            warnings.warn("lxml cannot represent null or non-xml doctype", DataLossWarning)
        doctype = self.doctypeClass(name, publicId, systemId)
        self.doctype = doctype
    
    def insertCommentInitial(self, data, parent=None):
        self.initial_comments.append(data)
    
    def insertRoot(self, name):
        """Create the document root"""
        #Because of the way libxml2 works, it doesn't seem to be possible to
        #alter information like the doctype after the tree has been parsed. 
        #Therefore we need to use the built-in parser to create our iniial 
        #tree, after which we can add elements like normal
        docStr = ""
        if self.doctype and self.doctype.name:
            docStr += "<!DOCTYPE %s"%self.doctype.name
            if self.doctype.publicId is not None or self.doctype.systemId is not None:
                docStr += ' PUBLIC "%s" "%s"'%(self.doctype.publicId or "",
                                               self.doctype.systemId or "")
            docStr += ">"
        docStr += "<html></html>"
        
        try:
            root = etree.fromstring(docStr)
        except etree.XMLSyntaxError:
            print docStr
            raise
        
        #Append the initial comments:
        for comment_data in self.initial_comments:
            root.addprevious(etree.Comment(comment_data))
        
        #Create the root document and add the ElementTree to it
        self.document = self.documentClass()
        self.document._elementTree = root.getroottree()
        
        #Add the root element to the internal child/open data structures
        root_element = self.elementClass(name)
        root_element._element = root
        self.document._childNodes.append(root_element)
        self.openElements.append(root_element)
    
        #Reset to the default insert comment function
        self.insertComment = super(TreeBuilder, self).insertComment
