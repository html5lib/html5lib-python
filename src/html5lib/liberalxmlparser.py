""" 
Warning: this module is experimental and subject to change and even removal
at any time. 

For background/rationale, see:
 * http://www.intertwingly.net/blog/2007/01/08/Xhtml5lib
 * http://tinyurl.com/ylfj8k (and follow-ups)

References:
 * http://googlereader.blogspot.com/2005/12/xml-errors-in-feeds.html
 * http://wiki.whatwg.org/wiki/HtmlVsXhtml

@@TODO:
 * Selectively lowercase only XHTML, but not foreign markup
"""

import sys

import html5parser
from constants import voidElements, contentModelFlags, tokenTypes

from xml.dom import XHTML_NAMESPACE
from xml.sax.saxutils import unescape

class XMLParser(html5parser.HTMLParser):
    """ liberal XML parser """

    def __init__(self, *args, **kwargs):
        html5parser.HTMLParser.__init__(self, *args, **kwargs)
        self.phases["initial"] = XmlRootPhase(self, self.tree)

    def normalizeToken(self, token):

        if token["type"] in (tokenTypes["StartTag"], tokenTypes["EmptyTag"]):
            token["data"] = dict(token["data"][::-1])

        # For EmptyTags, process both a Start and an End tag
        if token["type"] == tokenTypes["EmptyTag"]:
            save = self.tokenizer.contentModelFlag
            self.phase.processStartTag(token["name"], token["data"])
            self.tokenizer.contentModelFlag = save
            token["data"] = {}
            token["type"] = tokenTypes["EndTag"]

        elif token["type"] == tokenTypes["Characters"]:
            # un-escape rcdataElements (e.g. style, script)
            if self.tokenizer.contentModelFlag == contentModelFlags["CDATA"]:
                token["data"] = unescape(token["data"])

        elif token["type"] == tokenTypes["Comment"]:
            # Rescue CDATA from the comments
            if (token["data"].startswith("[CDATA[") and
                token["data"].endswith("]]")):
                token["type"] = "Characters"
                token["data"] = token["data"][7:-2]

        return token

    def _parse(self, stream, innerHTML=False, container="div", encoding=None,
               **kwargs):

        html5parser.HTMLParser._parse(self, stream, innerHTML, container,
                                      encoding, lowercaseElementName=False,
                                      lowercaseAttrName=False)

    def parseRCDataCData(self, name, attributes, contentType):
        self.tree.insertElement(name, attributes)

class XHTMLParser(XMLParser):
    """ liberal XMTHML parser """

    def __init__(self, *args, **kwargs):
        html5parser.HTMLParser.__init__(self, *args, **kwargs)
        self.phases["initial"] = XmlInitialPhase(self, self.tree)
        self.phases["beforeHtml"] = XhmlRootPhase(self, self.tree)

    def normalizeToken(self, token):
        token = XMLParser.normalizeToken(self, token)

        # ensure that non-void XHTML elements have content so that separate
        # open and close tags are emitted
        if token["type"]  == tokenTypes["EndTag"]:
            if token["name"] in voidElements:
                if not self.tree.openElements or \
                  self.tree.openElements[-1].name != token["name"]:
                    token["type"] = tokenTypes["EmptyTag"]
                    if not token.has_key("data"): token["data"] = {}
            else:
                if token["name"] == self.tree.openElements[-1].name and \
                  not self.tree.openElements[-1].hasContent():
                    for e in self.tree.openElements:
                        if 'xmlns' in e.attributes.keys():
                            if e.attributes['xmlns'] != XHTML_NAMESPACE:
                                break
                    else:
                        self.tree.insertText('')

        return token

class XhmlRootPhase(html5parser.BeforeHtmlPhase):
    def insertHtmlElement(self):
        element = self.tree.createElement("html", {'xmlns': 'http://www.w3.org/1999/xhtml'})
        self.tree.openElements.append(element)
        self.tree.document.appendChild(element)
        self.parser.phase = self.parser.phases["beforeHead"]

class XmlInitialPhase(html5parser.InitialPhase):
    """ Consume XML Prologs """
    def processComment(self, data):
        if not data.startswith('?xml') or not data.endswith('?'):
            html5parser.InitialPhase.processComment(self, data)

class XmlRootPhase(html5parser.Phase):
    """ Consume XML Prologs """
    def processEOF(self):
        pass

    def processComment(self, data):
        if not data.startswith('?xml') or not data.endswith('?'):
            html5parser.InitialPhase.processComment(self, data)

    """ Prime the Xml parser """
    def __getattr__(self, name):
        self.tree.openElements.append(self.tree.document)
        self.parser.phase = XmlElementPhase(self.parser, self.tree)
        return getattr(self.parser.phase, name)

class XmlElementPhase(html5parser.Phase):
    """ Generic handling for all XML elements """

    def __init__(self, *args, **kwargs):
        html5parser.Phase.__init__(self, *args, **kwargs)
        self.startTagHandler = html5parser.utils.MethodDispatcher([])
        self.startTagHandler.default = self.startTagOther
        self.endTagHandler = html5parser.utils.MethodDispatcher([])
        self.endTagHandler.default = self.endTagOther

    def startTagOther(self, name, attributes):
        element = self.tree.createElement(name, attributes)
        self.tree.openElements[-1].appendChild(element)
        self.tree.openElements.append(element)

    def endTagOther(self, name):
        for node in self.tree.openElements[::-1]:
            if node.name == name:
                while self.tree.openElements.pop() != node:
                    pass
                break
            else:
                self.parser.parseError()

    def processEOF(self):
        pass

    def processCharacters(self, data):
        self.tree.insertText(data)
