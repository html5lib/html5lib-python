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

import html5parser
from constants import voidElements
import gettext
_ = gettext.gettext

class XMLParser(html5parser.HTMLParser):
    """ liberal XML parser """

    def __init__(self, *args, **kwargs):
        html5parser.HTMLParser.__init__(self, *args, **kwargs)
        self.phases["initial"] = XmlRootPhase(self, self.tree)

    def normalizeToken(self, token):
        if token["type"] == "StartTag" or token["type"] == "EmptyTag":
            # We need to remove the duplicate attributes and convert attributes
            # to a dict so that [["x", "y"], ["x", "z"]] becomes {"x": "y"}

            # AT When Python 2.4 is widespread we should use
            # dict(reversed(token.data))
            token["data"] = dict(token["data"][::-1])

            # For EmptyTags, process both a Start and an End tag
            if token["type"] == "EmptyTag":
                self.phase.processStartTag(token["name"], token["data"])
                token["data"] = {}
                token["type"] = "EndTag"

        elif token["type"] == "EndTag":
            if token["data"]:
               self.parseError(_("End tag contains unexpected attributes."))

        elif token["type"] == "Comment":
            # Rescue CDATA from the comments
            if (token["data"].startswith("[CDATA[") and
                token["data"].endswith("]]")):
                token["type"] = "Characters"
                token["data"] = token["data"][7:-2]

        return token

class XHTMLParser(XMLParser):
    """ liberal XMTHML parser """

    def __init__(self, *args, **kwargs):
        html5parser.HTMLParser.__init__(self, *args, **kwargs)
        self.phases["rootElement"] = XhmlRootPhase(self, self.tree)

    def normalizeToken(self, token):
        token = XMLParser.normalizeToken(self, token)

        # ensure that non-void XHTML elements have content so that separate
        # open and close tags are emitted
        if token["type"]  == "EndTag" and \
            token["name"] not in voidElements and \
            token["name"] == self.tree.openElements[-1].name and \
            not self.tree.openElements[-1].hasContent():
            for e in self.tree.openElements:
                if 'xmlns' in e.attributes.keys():
                    if e.attributes['xmlns'] <> 'http://www.w3.org/1999/xhtml':
                        break
            else:
                self.tree.insertText('')

        return token

class XhmlRootPhase(html5parser.RootElementPhase):
    def insertHtmlElement(self):
        element = self.tree.createElement("html", {'xmlns': 'http://www.w3.org/1999/xhtml'})
        self.tree.openElements.append(element)
        self.tree.document.appendChild(element)
        self.parser.phase = self.parser.phases["beforeHead"]

class XmlRootPhase(html5parser.Phase):
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
                #XXX Something is wrong here... The next (commented) line is
                #html-only
                #self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != name:
                    self.parser.parseError(_("Unexpected end tag " + name +\
                      "."))
                while self.tree.openElements.pop() != node:
                    pass
                break
            else:
                self.parser.parseError()

    def processCharacters(self, data):
        self.tree.insertText(data)
