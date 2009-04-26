try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset
import sys

import inputstream
import tokenizer

import treebuilders
from treebuilders._base import Marker
from treebuilders import simpletree

import utils
from constants import contentModelFlags, spaceCharacters, asciiUpper2Lower
from constants import scopingElements, formattingElements, specialElements
from constants import headingElements, tableInsertModeElements
from constants import cdataElements, rcdataElements, voidElements
from constants import tokenTypes, ReparseException

def parse(doc, treebuilder="simpletree", encoding=None):
    tb = treebuilders.getTreeBuilder(treebuilder)
    p = HTMLParser(tb)
    return p.parse(doc, encoding=encoding)

class HTMLParser(object):
    """HTML parser. Generates a tree structure from a stream of (possibly
        malformed) HTML"""

    def __init__(self, tree = simpletree.TreeBuilder,
                 tokenizer = tokenizer.HTMLTokenizer, strict = False):
        """
        strict - raise an exception when a parse error is encountered

        tree - a treebuilder class controlling the type of tree that will be
        returned. Built in treebuilders can be accessed through
        html5lib.treebuilders.getTreeBuilder(treeType)
        
        tokenizer - a class that provides a stream of tokens to the treebuilder.
        This may be replaced for e.g. a sanitizer which converts some tags to
        text
        """

        # Raise an exception on the first error encountered
        self.strict = strict

        self.tree = tree()
        self.tokenizer_class = tokenizer
        self.errors = []

        # "quirks" / "limited-quirks" / "no-quirks"
        self.compatMode = "no quirks"

        self.phases = {
            "initial": InitialPhase(self, self.tree),
            "beforeHtml": BeforeHtmlPhase(self, self.tree),
            "beforeHead": BeforeHeadPhase(self, self.tree),
            "inHead": InHeadPhase(self, self.tree),
            # XXX "inHeadNoscript": InHeadNoScriptPhase(self, self.tree),
            "afterHead": AfterHeadPhase(self, self.tree),
            "inBody": InBodyPhase(self, self.tree),
            "inCDataRCData": InCDataRCDataPhase(self, self.tree),
            "inTable": InTablePhase(self, self.tree),
            "inCaption": InCaptionPhase(self, self.tree),
            "inColumnGroup": InColumnGroupPhase(self, self.tree),
            "inTableBody": InTableBodyPhase(self, self.tree),
            "inRow": InRowPhase(self, self.tree),
            "inCell": InCellPhase(self, self.tree),
            "inSelect": InSelectPhase(self, self.tree),
            "inSelectInTable": InSelectInTablePhase(self, self.tree),
            "afterBody": AfterBodyPhase(self, self.tree),
            "inFrameset": InFramesetPhase(self, self.tree),
            "afterFrameset": AfterFramesetPhase(self, self.tree),
            "afterAfterBody": AfterAfterBodyPhase(self, self.tree),
            "afterAfterFrameset": AfterAfterFramesetPhase(self, self.tree),
            # XXX after after frameset
        }

    def _parse(self, stream, innerHTML=False, container="div",
               encoding=None, parseMeta=True, useChardet=True, **kwargs):

        self.innerHTMLMode = innerHTML
        self.container = container
        self.tokenizer = self.tokenizer_class(stream, encoding=encoding,
                                              parseMeta=parseMeta,
                                              useChardet=useChardet, **kwargs)
        self.reset()

        while True:
            try:
                self.mainLoop()
                break
            except ReparseException, e:
                self.reset()

    def reset(self):
        self.tree.reset()
        self.firstStartTag = False
        self.errors = []
        self.compatMode = "no quirks"

        if self.innerHTMLMode:
            self.innerHTML = self.container.lower()

            if self.innerHTML in cdataElements:
                self.tokenizer.contentModelFlag = tokenizer.contentModelFlags["RCDATA"]
            elif self.innerHTML in rcdataElements:
                self.tokenizer.contentModelFlag = tokenizer.contentModelFlags["CDATA"]
            elif self.innerHTML == 'plaintext':
                self.tokenizer.contentModelFlag = tokenizer.contentModelFlags["PLAINTEXT"]
            else:
                # contentModelFlag already is PCDATA
                #self.tokenizer.contentModelFlag = tokenizer.contentModelFlags["PCDATA"]
                pass
            self.phase = self.phases["beforeHtml"]
            self.phase.insertHtmlElement()
            self.resetInsertionMode()
        else:
            self.innerHTML = False
            self.phase = self.phases["initial"]

        # We only seem to have InBodyPhase testcases where the following is
        # relevant ... need others too
        self.lastPhase = None
        self.beforeRCDataPhase = None
        
    def mainLoop(self):
        (CharactersToken, 
         SpaceCharactersToken, 
         StartTagToken,
         EndTagToken, 
         CommentToken,
         DoctypeToken) = (tokenTypes["Characters"],
                          tokenTypes["SpaceCharacters"],
                          tokenTypes["StartTag"],
                          tokenTypes["EndTag"],
                          tokenTypes["Comment"],
                          tokenTypes["Doctype"])

        for token in self.normalizedTokens():
            type = token["type"]
            if type == CharactersToken:
                self.phase.processCharacters(token["data"])
            elif type == SpaceCharactersToken:
                self.phase.processSpaceCharacters(token["data"])
            elif type == StartTagToken:
                self.phase.processStartTag(token["name"], token["data"])
            elif type == EndTagToken:
                self.phase.processEndTag(token["name"])
            elif type == CommentToken:
                self.phase.processComment(token["data"])
            elif type == DoctypeToken:
                self.phase.processDoctype(token["name"], token["publicId"],
                token["systemId"], token["correct"])
            else:
                self.parseError(token["data"], token.get("datavars", {}))

        # When the loop finishes it's EOF
        self.phase.processEOF()

    def normalizedTokens(self):
        for token in self.tokenizer:
            yield self.normalizeToken(token)

    def parse(self, stream, encoding=None, parseMeta=True, useChardet=True):
        """Parse a HTML document into a well-formed tree

        stream - a filelike object or string containing the HTML to be parsed

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        self._parse(stream, innerHTML=False, encoding=encoding)
        return self.tree.getDocument()
    
    def parseFragment(self, stream, container="div", encoding=None,
                      parseMeta=False, useChardet=True):
        """Parse a HTML fragment into a well-formed tree fragment
        
        container - name of the element we're setting the innerHTML property
        if set to None, default to 'div'

        stream - a filelike object or string containing the HTML to be parsed

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        self._parse(stream, True, container=container, encoding=encoding)
        return self.tree.getFragment()

    def parseError(self, errorcode="XXX-undefined-error", datavars={}):
        # XXX The idea is to make errorcode mandatory.
        self.errors.append((self.tokenizer.stream.position(), errorcode, datavars))
        if self.strict:
            raise ParseError

    def normalizeToken(self, token):
        """ HTML5 specific normalizations to the token stream """

        if token["type"] == tokenTypes["EmptyTag"]:
            # When a solidus (/) is encountered within a tag name what happens
            # depends on whether the current tag name matches that of a void
            # element.  If it matches a void element atheists did the wrong
            # thing and if it doesn't it's wrong for everyone.

            if token["name"] not in voidElements:
                self.parseError("incorrectly-placed-solidus")

            token["type"] = tokenTypes["StartTag"]

        if token["type"] == tokenTypes["StartTag"]:
            token["data"] = dict(token["data"][::-1])

        return token


    def resetInsertionMode(self):
        # The name of this method is mostly historical. (It's also used in the
        # specification.)
        last = False
        newModes = {
            "select":"inSelect",
            "td":"inCell",
            "th":"inCell",
            "tr":"inRow",
            "tbody":"inTableBody",
            "thead":"inTableBody",
            "tfoot":"inTableBody",
            "caption":"inCaption",
            "colgroup":"inColumnGroup",
            "table":"inTable",
            "head":"inBody",
            "body":"inBody",
            "frameset":"inFrameset"
        }
        for node in self.tree.openElements[::-1]:
            nodeName = node.name
            if node == self.tree.openElements[0]:
                last = True
                if nodeName not in ['td', 'th']:
                    # XXX
                    assert self.innerHTML
                    nodeName = self.innerHTML
            # Check for conditions that should only happen in the innerHTML
            # case
            if nodeName in ("select", "colgroup", "head", "frameset"):
                # XXX
                assert self.innerHTML
            if nodeName in newModes:
                self.phase = self.phases[newModes[nodeName]]
                break
            elif nodeName == "html":
                if self.tree.headPointer is None:
                    self.phase = self.phases["beforeHead"]
                else:
                   self.phase = self.phases["afterHead"]
                break
            elif last:
                self.phase = self.phases["inBody"]
                break

    def parseRCDataCData(self, name, attributes, contentType):
        """Generic (R)CDATA Parsing algorithm
        contentType - RCDATA or CDATA
        """
        assert contentType in ("CDATA", "RCDATA")
        
        element = self.tree.insertElement(name, attributes)
        self.tokenizer.contentModelFlag = contentModelFlags[contentType]

        self.originalPhase = self.phase

        self.phase = self.phases["inCDataRCData"]

class Phase(object):
    """Base class for helper object that implements each phase of processing
    """
    # Order should be (they can be omitted):
    # * EOF
    # * Comment
    # * Doctype
    # * SpaceCharacters
    # * Characters
    # * StartTag
    #   - startTag* methods
    # * EndTag
    #   - endTag* methods

    def __init__(self, parser, tree):
        self.parser = parser
        self.tree = tree

    def processEOF(self):
        raise NotImplementedError

    def processComment(self, data):
        # For most phases the following is correct. Where it's not it will be
        # overridden.
        self.tree.insertComment(data, self.tree.openElements[-1])

    def processDoctype(self, name, publicId, systemId, correct):
        self.parser.parseError("unexpected-doctype")

    def processSpaceCharacters(self, data):
        self.tree.insertText(data)

    def processStartTag(self, name, attributes):
        self.startTagHandler[name](name, attributes)

    def startTagHtml(self, name, attributes):
        if self.parser.firstStartTag == False and name == "html":
           self.parser.parseError("non-html-root")
        # XXX Need a check here to see if the first start tag token emitted is
        # this token... If it's not, invoke self.parser.parseError().
        for attr, value in attributes.iteritems():
            if attr not in self.tree.openElements[0].attributes:
                self.tree.openElements[0].attributes[attr] = value
        self.parser.firstStartTag = False

    def processEndTag(self, name):
        self.endTagHandler[name](name)

class InitialPhase(Phase):
    # This phase deals with error handling as well which is currently not
    # covered in the specification. The error handling is typically known as
    # "quirks mode". It is expected that a future version of HTML5 will defin
    # this.
    def processEOF(self):
        self.parser.parseError("expected-doctype-but-got-eof")
        self.parser.compatMode = "quirks"
        self.parser.phase = self.parser.phases["beforeHtml"]
        self.parser.phase.processEOF()

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processDoctype(self, name, publicId, systemId, correct):
        nameLower = name.translate(asciiUpper2Lower)
        if (nameLower != "html" or publicId != None or
            systemId != None):
            self.parser.parseError("unknown-doctype")
        
        if publicId is None:
            publicId = ""
        if systemId is None:
            systemId = ""
            
        self.tree.insertDoctype(name, publicId, systemId)

        if publicId != "":
            publicId = publicId.translate(asciiUpper2Lower)


        if ((not correct) or nameLower != "html"
            or publicId in
            ("+//silmaril//dtd html pro v0r11 19970101//en",
             "-//advasoft ltd//dtd html 3.0 aswedit + extensions//en",
             "-//as//dtd html 3.0 aswedit + extensions//en",
             "-//ietf//dtd html 2.0 level 1//en",
             "-//ietf//dtd html 2.0 level 2//en",
             "-//ietf//dtd html 2.0 strict level 1//en",
             "-//ietf//dtd html 2.0 strict level 2//en",
             "-//ietf//dtd html 2.0 strict//en",
             "-//ietf//dtd html 2.0//en",
             "-//ietf//dtd html 2.1e//en",
             "-//ietf//dtd html 3.0//en",
             "-//ietf//dtd html 3.0//en//",
             "-//ietf//dtd html 3.2 final//en",
             "-//ietf//dtd html 3.2//en",
             "-//ietf//dtd html 3//en",
             "-//ietf//dtd html level 0//en",
             "-//ietf//dtd html level 0//en//2.0",
             "-//ietf//dtd html level 1//en",
             "-//ietf//dtd html level 1//en//2.0",
             "-//ietf//dtd html level 2//en",
             "-//ietf//dtd html level 2//en//2.0",
             "-//ietf//dtd html level 3//en",
             "-//ietf//dtd html level 3//en//3.0",
             "-//ietf//dtd html strict level 0//en",
             "-//ietf//dtd html strict level 0//en//2.0",
             "-//ietf//dtd html strict level 1//en",
             "-//ietf//dtd html strict level 1//en//2.0",
             "-//ietf//dtd html strict level 2//en",
             "-//ietf//dtd html strict level 2//en//2.0",
             "-//ietf//dtd html strict level 3//en",
             "-//ietf//dtd html strict level 3//en//3.0",
             "-//ietf//dtd html strict//en",
             "-//ietf//dtd html strict//en//2.0",
             "-//ietf//dtd html strict//en//3.0",
             "-//ietf//dtd html//en",
             "-//ietf//dtd html//en//2.0",
             "-//ietf//dtd html//en//3.0",
             "-//metrius//dtd metrius presentational//en",
             "-//microsoft//dtd internet explorer 2.0 html strict//en",
             "-//microsoft//dtd internet explorer 2.0 html//en",
             "-//microsoft//dtd internet explorer 2.0 tables//en",
             "-//microsoft//dtd internet explorer 3.0 html strict//en",
             "-//microsoft//dtd internet explorer 3.0 html//en",
             "-//microsoft//dtd internet explorer 3.0 tables//en",
             "-//netscape comm. corp.//dtd html//en",
             "-//netscape comm. corp.//dtd strict html//en",
             "-//o'reilly and associates//dtd html 2.0//en",
             "-//o'reilly and associates//dtd html extended 1.0//en",
             "-//spyglass//dtd html 2.0 extended//en",
             "-//sq//dtd html 2.0 hotmetal + extensions//en",
             "-//sun microsystems corp.//dtd hotjava html//en",
             "-//sun microsystems corp.//dtd hotjava strict html//en",
             "-//w3c//dtd html 3 1995-03-24//en",
             "-//w3c//dtd html 3.2 draft//en",
             "-//w3c//dtd html 3.2 final//en",
             "-//w3c//dtd html 3.2//en",
             "-//w3c//dtd html 3.2s draft//en",
             "-//w3c//dtd html 4.0 frameset//en",
             "-//w3c//dtd html 4.0 transitional//en",
             "-//w3c//dtd html experimental 19960712//en",
             "-//w3c//dtd html experimental 970421//en",
             "-//w3c//dtd w3 html//en",
             "-//w3o//dtd w3 html 3.0//en",
             "-//w3o//dtd w3 html 3.0//en//",
             "-//w3o//dtd w3 html strict 3.0//en//",
             "-//webtechs//dtd mozilla html 2.0//en",
             "-//webtechs//dtd mozilla html//en",
             "-/w3c/dtd html 4.0 transitional/en",
             "html")
            or (publicId in
                ("-//w3c//dtd html 4.01 frameset//EN",
                 "-//w3c//dtd html 4.01 transitional//EN") and systemId == None)
            or (systemId != None and
              systemId == 
                "http://www.ibm.com/data/dtd/v11/ibmxhtml1-transitional.dtd")):
            self.parser.compatMode = "quirks"
        elif (publicId in
              ("-//w3c//dtd xhtml 1.0 frameset//EN",
               "-//w3c//dtd xhtml 1.0 transitional//EN")
              or (publicId in
                  ("-//w3c//dtd html 4.01 frameset//EN",
                   "-//w3c//dtd html 4.01 transitional//EN") and systemId == None)):
            self.parser.compatMode = "limited quirks"

        self.parser.phase = self.parser.phases["beforeHtml"]

    def processSpaceCharacters(self, data):
        pass

    def processCharacters(self, data):
        self.parser.parseError("expected-doctype-but-got-chars")
        self.parser.compatMode = "quirks"
        self.parser.phase = self.parser.phases["beforeHtml"]
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.parseError("expected-doctype-but-got-start-tag",
          {"name": name})
        self.parser.compatMode = "quirks"
        self.parser.phase = self.parser.phases["beforeHtml"]
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError("expected-doctype-but-got-end-tag",
          {"name": name})
        self.parser.compatMode = "quirks"
        self.parser.phase = self.parser.phases["beforeHtml"]
        self.parser.phase.processEndTag(name)


class BeforeHtmlPhase(Phase):
    # helper methods
    def insertHtmlElement(self):
        self.tree.insertRoot("html")
        self.parser.phase = self.parser.phases["beforeHead"]

    # other
    def processEOF(self):
        self.insertHtmlElement()
        self.parser.phase.processEOF()

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processSpaceCharacters(self, data):
        pass

    def processCharacters(self, data):
        self.insertHtmlElement()
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        if name == "html":
            self.parser.firstStartTag = True
        self.insertHtmlElement()
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.insertHtmlElement()
        self.parser.phase.processEndTag(name)


class BeforeHeadPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("head", self.startTagHead)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            (("head", "br"), self.endTagImplyHead)
        ])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        self.startTagHead("head", {})
        self.parser.phase.processEOF()

    def processSpaceCharacters(self, data):
        pass

    def processCharacters(self, data):
        self.startTagHead("head", {})
        self.parser.phase.processCharacters(data)

    def startTagHead(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.headPointer = self.tree.openElements[-1]
        self.parser.phase = self.parser.phases["inHead"]

    def startTagOther(self, name, attributes):
        self.startTagHead("head", {})
        self.parser.phase.processStartTag(name, attributes)

    def endTagImplyHead(self, name):
        self.startTagHead("head", {})
        self.parser.phase.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError("end-tag-after-implied-root",
          {"name": name})

class InHeadPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler =  utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("title", self.startTagTitle),
            (("noscript", "noframes", "style"), self.startTagNoScriptNoFramesStyle),
            ("script", self.startTagScript),
            (("base", "link", "command", "eventsource"), 
             self.startTagBaseLinkCommandEventsource),
            ("meta", self.startTagMeta),
            ("head", self.startTagHead)
        ])
        self.startTagHandler.default = self.startTagOther

        self. endTagHandler = utils.MethodDispatcher([
            ("head", self.endTagHead),
            ("br", self.endTagBr)
        ])
        self.endTagHandler.default = self.endTagOther

    # helper
    def appendToHead(self, element):
        if self.tree.headPointer is not None:
            self.tree.headPointer.appendChild(element)
        else:
            assert self.parser.innerHTML
            self.tree.openElements[-1].appendChild(element)

    # the real thing
    def processEOF (self):
        self.anythingElse()
        self.parser.phase.processEOF()

    def processCharacters(self, data):
        self.anythingElse()
        self.parser.phase.processCharacters(data)

    def startTagHtml(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagHead(self, name, attributes):
        self.parser.parseError("two-heads-are-not-better-than-one")

    def startTagBaseLinkCommandEventsource(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()
        #XXX Acknowledge self closing flag

    def startTagMeta(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()
        #XXX Acknowledge self closing flag

        if self.parser.tokenizer.stream.charEncoding[1] == "tentative":
            if "charset" in attributes:
                self.parser.tokenizer.stream.changeEncoding(attributes["charset"])
            elif "content" in attributes:
                data = inputstream.EncodingBytes(
                    attributes["content"].encode(self.parser.tokenizer.stream.charEncoding[0]))
                parser = inputstream.ContentAttrParser(data)
                codec = parser.parse()
                self.parser.tokenizer.stream.changeEncoding(codec)

    def startTagTitle(self, name, attributes):
        self.parser.parseRCDataCData(name, attributes, "RCDATA")

    def startTagNoScriptNoFramesStyle(self, name, attributes):
        #Need to decide whether to implement the scripting-disabled case
        self.parser.parseRCDataCData(name, attributes, "CDATA")

    def startTagScript(self, name, attributes):
        #I think this is equivalent to the CDATA stuff since we don't execute script
        #self.tree.insertElement(name, attributes)
        self.parser.parseRCDataCData(name, attributes, "CDATA")

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.phase.processStartTag(name, attributes)

    def endTagHead(self, name):
        node = self.parser.tree.openElements.pop()
        assert node.name == "head"
        self.parser.phase = self.parser.phases["afterHead"]

    def endTagBr(self, name):
        self.anythingElse()
        self.parser.phase.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag", {"name": name})

    def anythingElse(self):
        self.endTagHead("head")
        

# XXX If we implement a parser for which scripting is disabled we need to
# implement this phase.
#
# class InHeadNoScriptPhase(Phase):

class AfterHeadPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("body", self.startTagBody),
            ("frameset", self.startTagFrameset),
            (("base", "link", "meta", "noframes", "script", "style", "title"),
              self.startTagFromHead),
            ("head", self.startTagHead)
        ])
        self.startTagHandler.default = self.startTagOther
        self.endTagHandler = utils.MethodDispatcher([("br", self.endTagBr)])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        self.anythingElse()
        self.parser.phase.processEOF()

    def processCharacters(self, data):
        self.anythingElse()
        self.parser.phase.processCharacters(data)

    def startTagBody(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inBody"]

    def startTagFrameset(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inFrameset"]

    def startTagFromHead(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-out-of-my-head",
          {"name": name})
        self.tree.openElements.append(self.tree.headPointer)
        self.parser.phases["inHead"].processStartTag(name, attributes)
        for node in self.tree.openElements[::-1]:
            if node.name == "head":
                self.tree.openElements.remove(node)
                break

    def startTagHead(self, name, attributes):
        self.parser.parseError("unexpected-start-tag", {"name":name})

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.phase.processStartTag(name, attributes)

    def endTagBr(self, name):
        #This is not currently in the spec
        self.anythingElse()
        self.parser.phase.processEndTag("br")

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag", {"name":name})

    def anythingElse(self):
        self.tree.insertElement("body", {})
        self.parser.phase = self.parser.phases["inBody"]


class InBodyPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-body
    # the crazy mode
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        #Keep a ref to this for special handling of whitespace in <pre>
        self.processSpaceCharactersNonPre = self.processSpaceCharacters

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            (("base", "link", "meta", "script", "style", "title"),
              self.startTagProcessInHead),
            ("body", self.startTagBody),
            (("address", "article", "aside", "blockquote", "center", "datagrid",
              "details", "dialog", "dir", "div", "dl", "fieldset", "figure",
              "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "listing",
              "menu", "nav", "ol", "p", "pre", "section", "ul"),
              self.startTagCloseP),
            ("form", self.startTagForm),
            (("li", "dd", "dt"), self.startTagListItem),
            ("plaintext",self.startTagPlaintext),
            (headingElements, self.startTagHeading),
            ("a", self.startTagA),
            (("b", "big", "em", "font", "i", "s", "small", "strike", "strong",
              "tt", "u"),self.startTagFormatting),
            ("nobr", self.startTagNobr),
            ("button", self.startTagButton),
            (("applet", "marquee", "object"), self.startTagAppletMarqueeObject),
            ("xmp", self.startTagXmp),
            ("table", self.startTagTable),
            (("area", "basefont", "bgsound", "br", "embed", "img", "param",
              "spacer", "wbr"), self.startTagVoidFormatting),
            ("hr", self.startTagHr),
            ("image", self.startTagImage),
            ("input", self.startTagInput),
            ("isindex", self.startTagIsIndex),
            ("textarea", self.startTagTextarea),
            (("iframe", "noembed", "noframes", "noscript"), self.startTagCdata),
            ("select", self.startTagSelect),
            (("rp", "rt"), self.startTagRpRt),
            (("option", "optgroup"), self.startTagOpt),
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "tbody", "td", "tfoot", "th", "thead",
              "tr"), self.startTagMisplaced),
            (("event-source", "command"), self.startTagNew)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("body",self.endTagBody),
            ("html",self.endTagHtml),
            (("address", "article", "aside", "blockquote", "center", "datagrid",
              "details", "dialog", "dir", "div", "dl", "fieldset", "figure",
              "footer", "header", "listing", "menu", "nav", "ol", "pre", "section",
              "ul"), self.endTagBlock),
            ("form", self.endTagForm),
            ("p",self.endTagP),
            (("dd", "dt", "li"), self.endTagListItem),
            (headingElements, self.endTagHeading),
            (("a", "b", "big", "em", "font", "i", "nobr", "s", "small",
              "strike", "strong", "tt", "u"), self.endTagFormatting),
            (("applet", "button", "marquee", "object"), self.endTagAppletButtonMarqueeObject),
            ("br", self.endTagBr),
            ])
        self.endTagHandler.default = self.endTagOther

    # helper
    def addFormattingElement(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.activeFormattingElements.append(
            self.tree.openElements[-1])

    # the real deal
    def processEOF(self):
        allowed_elements = frozenset(("dd", "dt", "li", "p", "tbody", "td",
                                      "tfoot", "th", "thead", "tr", "body",
                                      "html"))
        for node in self.tree.openElements[::-1]:
            if node.name not in allowed_elements:
                self.parser.parseError("expected-closing-tag-but-got-eof")
                break
        #Stop parsing
    
    def processSpaceCharactersDropNewline(self, data):
        # Sometimes (start of <pre>, <listing>, and <textarea> blocks) we
        # want to drop leading newlines
        self.processSpaceCharacters = self.processSpaceCharactersNonPre
        if (data.startswith("\n") and
            self.tree.openElements[-1].name in ("pre", "listing", "textarea") and
            not self.tree.openElements[-1].hasContent()):
            data = data[1:]
        if data:
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertText(data)

    def processCharacters(self, data):
        # XXX The specification says to do this for every character at the
        # moment, but apparently that doesn't match the real world so we don't
        # do it for space characters.
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertText(data)

    #This matches the current spec but may not match the real world
    def processSpaceCharacters(self, data):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertText(data)

    def startTagProcessInHead(self, name, attributes):
        self.parser.phases["inHead"].processStartTag(name, attributes)

    def startTagBody(self, name, attributes):
        self.parser.parseError("unexpected-start-tag", {"name": "body"})
        if (len(self.tree.openElements) == 1
            or self.tree.openElements[1].name != "body"):
            assert self.parser.innerHTML
        else:
            for attr, value in attributes.iteritems():
                if attr not in self.tree.openElements[1].attributes:
                    self.tree.openElements[1].attributes[attr] = value

    def startTagCloseP(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        self.tree.insertElement(name, attributes)
        if name in ("pre", "listing"):
            self.processSpaceCharacters = self.processSpaceCharactersDropNewline

    def startTagForm(self, name, attributes):
        if self.tree.formPointer:
            self.parser.parseError(u"unexpected-start-tag", {"name": "form"})
        else:
            if self.tree.elementInScope("p"):
                self.endTagP("p")
            self.tree.insertElement(name, attributes)
            self.tree.formPointer = self.tree.openElements[-1]

    def startTagListItem(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        stopNames = {"li":("li"), "dd":("dd", "dt"), "dt":("dd", "dt")}
        stopName = stopNames[name]
        # AT Use reversed in Python 2.4...
        for i, node in enumerate(self.tree.openElements[::-1]):
            if node.name in stopName:
                poppedNodes = []
                for j in range(i+1):
                    poppedNodes.append(self.tree.openElements.pop())
                if i >= 1:
                    self.parser.parseError(
                        i == 1 and "missing-end-tag" or "missing-end-tags",
                        {"name": u", ".join([item.name
                                             for item
                                             in poppedNodes[:-1]])})
                break
        

            # Phrasing elements are all non special, non scoping, non
            # formatting elements
            if (node.name in (specialElements | scopingElements)
              and node.name not in ("address", "div")):
                break
        # Always insert an <li> element.
        self.tree.insertElement(name, attributes)

    def startTagPlaintext(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        self.tree.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["PLAINTEXT"]

    def startTagHeading(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        # Uncomment the following for IE7 behavior:
        #
        #for item in headingElements:
        #    if self.tree.elementInScope(item):
        #        self.parser.parseError("unexpected-start-tag", {"name": name})
        #        item = self.tree.openElements.pop()
        #        while item.name not in headingElements:
        #            item = self.tree.openElements.pop()
        #        break
        self.tree.insertElement(name, attributes)

    def startTagA(self, name, attributes):
        afeAElement = self.tree.elementInActiveFormattingElements("a")
        if afeAElement:
            self.parser.parseError("unexpected-start-tag-implies-end-tag",
              {"startName": "a", "endName": "a"})
            self.endTagFormatting("a")
            if afeAElement in self.tree.openElements:
                self.tree.openElements.remove(afeAElement)
            if afeAElement in self.tree.activeFormattingElements:
                self.tree.activeFormattingElements.remove(afeAElement)
        self.tree.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

    def startTagFormatting(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

    def startTagNobr(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        if self.tree.elementInScope("nobr"):
            self.parser.parseError("unexpected-start-tag-implies-end-tag",
              {"startName": "nobr", "endName": "nobr"})
            self.processEndTag("nobr")
            # XXX Need tests that trigger the following
            self.tree.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

    def startTagButton(self, name, attributes):
        if self.tree.elementInScope("button"):
            self.parser.parseError("unexpected-start-tag-implies-end-tag",
              {"startName": "button", "endName": "button"})
            self.processEndTag("button")
            self.parser.phase.processStartTag(name, attributes)
        else:
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(name, attributes)
            self.tree.activeFormattingElements.append(Marker)

    def startTagAppletMarqueeObject(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        self.tree.activeFormattingElements.append(Marker)

    def startTagXmp(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.parser.parseRCDataCData(name, attributes, "CDATA")

    def startTagTable(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.processEndTag("p")
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inTable"]

    def startTagVoidFormatting(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagHr(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagImage(self, name, attributes):
        # No really...
        self.parser.parseError("unexpected-start-tag-treated-as",
          {"originalName": "image", "newName": "img"})
        self.processStartTag("img", attributes)

    def startTagInput(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        if self.tree.formPointer:
            # XXX Not exactly sure what to do here
            self.tree.openElements[-1].form = self.tree.formPointer
        self.tree.openElements.pop()

    def startTagIsIndex(self, name, attributes):
        self.parser.parseError("deprecated-tag", {"name": "isindex"})
        if self.tree.formPointer:
            return
        self.processStartTag("form", {})
        self.processStartTag("hr", {})
        self.processStartTag("p", {})
        self.processStartTag("label", {})
        # XXX Localization ...
        self.processCharacters(
            "This is a searchable index. Insert your search keywords here: ")
        attributes["name"] = "isindex"
        attrs = [[key,value] for key,value in attributes.iteritems()]
        self.processStartTag("input", dict(attrs))
        self.processEndTag("label")
        self.processEndTag("p")
        self.processStartTag("hr", {})
        self.processEndTag("form")

    def startTagTextarea(self, name, attributes):
        # XXX Form element pointer checking here as well...
        self.tree.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["RCDATA"]
        self.processSpaceCharacters = self.processSpaceCharactersDropNewline

    def startTagCdata(self, name, attributes):
        """iframe, noembed noframes, noscript(if scripting enabled)"""
        self.parser.parseRCDataCData(name, attributes, "CDATA")

    def startTagOpt(self, name, attributes):
        if self.tree.elementInScope("option"):
            self.parser.phase.processEndTag("option")
        self.tree.reconstructActiveFormattingElements()
        self.parser.tree.insertElement(name, attributes)

    def startTagSelect(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        if self.parser.phase in (self.parser.phases["inTable"],
          self.parser.phases["inCaption"],
          self.parser.phases["inColumnGroup"],
          self.parser.phases["inTableBody"], self.parser.phases["inRow"],
          self.parser.phases["inCell"]):
            self.parser.phase = self.parser.phases["inSelectInTable"]
        else:
            self.parser.phase = self.parser.phases["inSelect"]

    def startTagRpRt(self, name, attributes):
        if self.tree.elementInScope("ruby"):
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != "ruby":
                self.parser.parseError()
                while self.tree.openElements[-1].name != "ruby":
                    self.tree.openElements.pop()
        self.tree.insertElement(name, attributes)

    def startTagMisplaced(self, name, attributes):
        """ Elements that should be children of other elements that have a
        different insertion mode; here they are ignored
        "caption", "col", "colgroup", "frame", "frameset", "head",
        "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
        "tr", "noscript"
        """
        self.parser.parseError("unexpected-start-tag-ignored", {"name": name})

    def startTagNew(self, name, attributes):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        #2007-08-30 - MAP - commenting out this write to sys.stderr because
        #  it's really annoying me when I run the validator tests
        #sys.stderr.write("Warning: Undefined behaviour for start tag %s"%name)
        self.startTagOther(name, attributes)
        #raise NotImplementedError

    def startTagOther(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)

    def endTagP(self, name):
        if self.tree.elementInScope("p"):
            self.tree.generateImpliedEndTags("p")
        if self.tree.openElements[-1].name != "p":
            self.parser.parseError("unexpected-end-tag", {"name": "p"})
        if self.tree.elementInScope("p"):
            while self.tree.elementInScope("p"):
                self.tree.openElements.pop()
        else:
            self.startTagCloseP("p", {})
            self.endTagP("p")

    def endTagBody(self, name):
        # XXX Need to take open <p> tags into account here. We shouldn't imply
        # </p> but we should not throw a parse error either. Specification is
        # likely to be updated.
        if (len(self.tree.openElements) == 1 or
            self.tree.openElements[1].name != "body"):
            # innerHTML case
            self.parser.parseError()
            return
        elif self.tree.openElements[-1].name != "body":
            for node in self.tree.openElements[2:]:
                if node.name not in frozenset(("dd", "dt", "li", "p",
                                               "tbody", "td", "tfoot",
                                               "th", "thead", "tr")):
                    #Not sure this is the correct name for the parse error
                    self.parser.parseError(
                        "expected-one-end-tag-but-got-another",
                        {"expectedName": "body", "gotName": node.name})
                    break
        self.parser.phase = self.parser.phases["afterBody"]

    def endTagHtml(self, name):
        self.endTagBody(name)
        if not self.parser.innerHTML:
            self.parser.phase.processEndTag(name)

    def endTagBlock(self, name):
        #Put us back in the right whitespace handling mode
        if name == "pre":
            self.processSpaceCharacters = self.processSpaceCharactersNonPre
        inScope = self.tree.elementInScope(name)
        if inScope:
            self.tree.generateImpliedEndTags()
        if self.tree.openElements[-1].name != name:
             self.parser.parseError("end-tag-too-early", {"name": name})
        if inScope:
            node = self.tree.openElements.pop()
            while node.name != name:
                node = self.tree.openElements.pop()

    def endTagForm(self, name):
        self.tree.formPointer = None
        if not self.tree.elementInScope(name):
            self.parser.parseError("unexpected-end-tag",
                                   {"name":"form"})
        else:
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != name:
                self.parser.parseError("end-tag-too-early-ignored",
                                       {"name": "form"})
            node = self.tree.openElements.pop()
            while node.name != name:
                node = self.tree.openElements.pop()

    def endTagListItem(self, name):
        # AT Could merge this with the Block case
        if self.tree.elementInScope(name):
            self.tree.generateImpliedEndTags(name)
        
        if self.tree.openElements[-1].name != name:
            self.parser.parseError("end-tag-too-early", {"name": name})

        if self.tree.elementInScope(name):
            node = self.tree.openElements.pop()
            while node.name != name:
                node = self.tree.openElements.pop()

    def endTagHeading(self, name):
        for item in headingElements:
            if self.tree.elementInScope(item):
                self.tree.generateImpliedEndTags()
                break
        if self.tree.openElements[-1].name != name:
            self.parser.parseError("end-tag-too-early", {"name": name})

        for item in headingElements:
            if self.tree.elementInScope(item):
                item = self.tree.openElements.pop()
                while item.name not in headingElements:
                    item = self.tree.openElements.pop()
                break

    def endTagFormatting(self, name):
        """The much-feared adoption agency algorithm
        """
        # http://www.whatwg.org/specs/web-apps/current-work/#adoptionAgency
        # XXX Better parseError messages appreciated.
        while True:
            # Step 1 paragraph 1
            afeElement = self.tree.elementInActiveFormattingElements(name)
            if not afeElement or (afeElement in self.tree.openElements and
              not self.tree.elementInScope(afeElement.name)):
                self.parser.parseError("adoption-agency-1.1", {"name": name})
                return

            # Step 1 paragraph 2
            elif afeElement not in self.tree.openElements:
                self.parser.parseError("adoption-agency-1.2", {"name": name})
                self.tree.activeFormattingElements.remove(afeElement)
                return

            # Step 1 paragraph 3
            if afeElement != self.tree.openElements[-1]:
                self.parser.parseError("adoption-agency-1.3", {"name": name})

            # Step 2
            # Start of the adoption agency algorithm proper
            afeIndex = self.tree.openElements.index(afeElement)
            furthestBlock = None
            for element in self.tree.openElements[afeIndex:]:
                if element.name in specialElements | scopingElements:
                    furthestBlock = element
                    break

            # Step 3
            if furthestBlock is None:
                element = self.tree.openElements.pop()
                while element != afeElement:
                    element = self.tree.openElements.pop()
                self.tree.activeFormattingElements.remove(element)
                return
            commonAncestor = self.tree.openElements[afeIndex-1]

            # Step 5
            if furthestBlock.parent:
                furthestBlock.parent.removeChild(furthestBlock)

            # Step 6
            # The bookmark is supposed to help us identify where to reinsert
            # nodes in step 12. We have to ensure that we reinsert nodes after
            # the node before the active formatting element. Note the bookmark
            # can move in step 7.4
            bookmark = self.tree.activeFormattingElements.index(afeElement)

            # Step 7
            lastNode = node = furthestBlock
            while True:
                # AT replace this with a function and recursion?
                # Node is element before node in open elements
                node = self.tree.openElements[
                    self.tree.openElements.index(node)-1]
                while node not in self.tree.activeFormattingElements:
                    tmpNode = node
                    node = self.tree.openElements[
                        self.tree.openElements.index(node)-1]
                    self.tree.openElements.remove(tmpNode)
                # Step 7.3
                if node == afeElement:
                    break
                # Step 7.4
                if lastNode == furthestBlock:
                    bookmark = self.tree.activeFormattingElements.\
                      index(node) + 1
                # Step 7.5
                cite = node.parent
                if node.hasContent():
                    clone = node.cloneNode()
                    # Replace node with clone
                    self.tree.activeFormattingElements[
                      self.tree.activeFormattingElements.index(node)] = clone
                    self.tree.openElements[
                      self.tree.openElements.index(node)] = clone
                    node = clone
                # Step 7.6
                # Remove lastNode from its parents, if any
                if lastNode.parent:
                    lastNode.parent.removeChild(lastNode)
                node.appendChild(lastNode)
                # Step 7.7
                lastNode = node
                # End of inner loop

            # Step 8
            if lastNode.parent:
                lastNode.parent.removeChild(lastNode)
            commonAncestor.appendChild(lastNode)

            # Step 9
            clone = afeElement.cloneNode()

            # Step 10
            furthestBlock.reparentChildren(clone)

            # Step 11
            furthestBlock.appendChild(clone)

            # Step 12
            self.tree.activeFormattingElements.remove(afeElement)
            self.tree.activeFormattingElements.insert(bookmark, clone)

            # Step 13
            self.tree.openElements.remove(afeElement)
            self.tree.openElements.insert(
              self.tree.openElements.index(furthestBlock) + 1, clone)

    def endTagAppletButtonMarqueeObject(self, name):
        if self.tree.elementInScope(name):
            self.tree.generateImpliedEndTags()
        if self.tree.openElements[-1].name != name:
            self.parser.parseError("end-tag-too-early", {"name": name})

        if self.tree.elementInScope(name):
            element = self.tree.openElements.pop()
            while element.name != name:
                element = self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()

    def endTagBr(self, name):
        self.parser.parseError("unexpected-end-tag-treated-as",
          {"originalName": "br", "newName": "br element"})
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, {})
        self.tree.openElements.pop()

    def endTagOther(self, name):
        for node in self.tree.openElements[::-1]:
            if node.name == name:
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != name:
                    self.parser.parseError("unexpected-end-tag", {"name": name})
                while self.tree.openElements.pop() != node:
                    pass
                break
            else:
                if node.name in specialElements | scopingElements:
                    self.parser.parseError("unexpected-end-tag", {"name": name})
                    break

class InCDataRCDataPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([])
        self.startTagHandler.default = self.startTagOther
        self.endTagHandler = utils.MethodDispatcher([
                ("script", self.endTagScript)])
        self.endTagHandler.default = self.endTagOther

    def processCharacters(self, data):
        self.tree.insertText(data)
    
    def processEOF(self):
        self.parser.parseError("expected-named-closing-tag-but-got-eof", 
                               self.tree.openElements[-1].name)
        self.tree.openElements.pop()
        self.parser.phase = self.parser.originalPhase
        self.parser.phase.processEOF()

    def startTagOther(self, name, attributes):
        assert False, "Tried to process start tag %s in (R)CDATA mode"%name

    def endTagScript(self, name):
        node = self.tree.openElements.pop()
        assert node.name == "script"
        self.parser.phase = self.parser.originalPhase
        #The rest of this method is all stuff that only happens if
        #document.write works
    
    def endTagOther(self, name):
        node = self.tree.openElements.pop()
        self.parser.phase = self.parser.originalPhase

class InTablePhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("caption", self.startTagCaption),
            ("colgroup", self.startTagColgroup),
            ("col", self.startTagCol),
            (("tbody", "tfoot", "thead"), self.startTagRowGroup),
            (("td", "th", "tr"), self.startTagImplyTbody),
            ("table", self.startTagTable),
            (("style", "script"), self.startTagStyleScript),
            ("input", self.startTagInput)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "tbody", "td",
              "tfoot", "th", "thead", "tr"), self.endTagIgnore)
        ])
        self.endTagHandler.default = self.endTagOther

    # helper methods
    def clearStackToTableContext(self):
        # "clear the stack back to a table context"
        while self.tree.openElements[-1].name not in ("table", "html"):
            #self.parser.parseError("unexpected-implied-end-tag-in-table",
            #  {"name":  self.tree.openElements[-1].name})
            self.tree.openElements.pop()
        # When the current node is <html> it's an innerHTML case

    def getCurrentTable(self):
        i = -1
        while self.tree.openElements[i].name != "table":
             i -= 1
        return self.tree.openElements[i]

    # processing methods
    def processEOF(self):
        if self.tree.openElements[-1].name != "html":
            self.parser.parseError("eof-in-table")
        else:
            assert self.parser.innerHTML
        #Stop parsing

    def processSpaceCharacters(self, data):
        if "tainted" not in self.getCurrentTable()._flags:
            self.tree.insertText(data)
        else:
            self.processCharacters(data)

    def processCharacters(self, data):
        if self.tree.openElements[-1].name in ("style", "script"):
           self.tree.insertText(data)
        else:
            if "tainted" not in self.getCurrentTable()._flags:
                self.parser.parseError("unexpected-char-implies-table-voodoo")
                self.getCurrentTable()._flags.append("tainted")
            # Do the table magic!
            self.tree.insertFromTable = True
            self.parser.phases["inBody"].processCharacters(data)
            self.tree.insertFromTable = False

    def startTagCaption(self, name, attributes):
        self.clearStackToTableContext()
        self.tree.activeFormattingElements.append(Marker)
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inCaption"]

    def startTagColgroup(self, name, attributes):
        self.clearStackToTableContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inColumnGroup"]

    def startTagCol(self, name, attributes):
        self.startTagColgroup("colgroup", {})
        self.parser.phase.processStartTag(name, attributes)

    def startTagRowGroup(self, name, attributes):
        self.clearStackToTableContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inTableBody"]

    def startTagImplyTbody(self, name, attributes):
        self.startTagRowGroup("tbody", {})
        self.parser.phase.processStartTag(name, attributes)

    def startTagTable(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-implies-end-tag",
          {"startName": "table", "endName": "table"})
        self.parser.phase.processEndTag("table")
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def startTagStyleScript(self, name, attributes):
        if "tainted" not in self.getCurrentTable()._flags:
            self.parser.phases["inHead"].processStartTag(name, attributes)
        else:
            self.startTagOther(name, attributes)

    def startTagInput(self, name, attributes):
        if "type" in attributes and attributes["type"].translate(asciiUpper2Lower) == "hidden" and "tainted" not in self.getCurrentTable()._flags:
            self.parser.parseError("unexpected-hidden-input-in-table")
            self.tree.insertElement(name, attributes)
            # XXX associate with form
            self.tree.openElements.pop()
        else:
            self.startTagOther(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-implies-table-voodoo", {"name": name})
        if "tainted" not in self.getCurrentTable()._flags:
            self.getCurrentTable()._flags.append("tainted")
        # Do the table magic!
        self.tree.insertFromTable = True
        self.parser.phases["inBody"].processStartTag(name, attributes)
        self.tree.insertFromTable = False

    def endTagTable(self, name):
        if self.tree.elementInScope("table", True):
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != "table":
                self.parser.parseError("end-tag-too-early-named",
                  {"gotName": "table",
                   "expectedName": self.tree.openElements[-1].name})
            while self.tree.openElements[-1].name != "table":
                self.tree.openElements.pop()
            self.tree.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            # innerHTML case
            assert self.parser.innerHTML
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError("unexpected-end-tag", {"name": name})

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag-implies-table-voodoo", {"name": name})
        if "tainted" not in self.getCurrentTable()._flags:
            self.getCurrentTable()._flags.append("tainted")
        # Do the table magic!
        self.tree.insertFromTable = True
        self.parser.phases["inBody"].processEndTag(name)
        self.tree.insertFromTable = False


class InCaptionPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-caption
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableElement)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("caption", self.endTagCaption),
            ("table", self.endTagTable),
            (("body", "col", "colgroup", "html", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.endTagIgnore)
        ])
        self.endTagHandler.default = self.endTagOther

    def ignoreEndTagCaption(self):
        return not self.tree.elementInScope("caption", True)

    def processEOF(self):
        self.parser.phases["inBody"].processEOF()

    def processCharacters(self, data):
        self.parser.phases["inBody"].processCharacters(data)

    def startTagTableElement(self, name, attributes):
        self.parser.parseError()
        #XXX Have to duplicate logic here to find out if the tag is ignored
        ignoreEndTag = self.ignoreEndTagCaption()
        self.parser.phase.processEndTag("caption")
        if not ignoreEndTag:
            self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def endTagCaption(self, name):
        if not self.ignoreEndTagCaption():
            # AT this code is quite similar to endTagTable in "InTable"
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != "caption":
                self.parser.parseError("expected-one-end-tag-but-got-another",
                  {"gotName": "caption",
                   "expectedName": self.tree.openElements[-1].name})
            while self.tree.openElements[-1].name != "caption":
                self.tree.openElements.pop()
            self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()
            self.parser.phase = self.parser.phases["inTable"]
        else:
            # innerHTML case
            assert self.parser.innerHTML
            self.parser.parseError()

    def endTagTable(self, name):
        self.parser.parseError()
        ignoreEndTag = self.ignoreEndTagCaption()
        self.parser.phase.processEndTag("caption")
        if not ignoreEndTag:
            self.parser.phase.processEndTag(name)

    def endTagIgnore(self, name):
        self.parser.parseError("unexpected-end-tag", {"name": name})

    def endTagOther(self, name):
        self.parser.phases["inBody"].processEndTag(name)


class InColumnGroupPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-column

    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("col", self.startTagCol)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("colgroup", self.endTagColgroup),
            ("col", self.endTagCol)
        ])
        self.endTagHandler.default = self.endTagOther

    def ignoreEndTagColgroup(self):
        return self.tree.openElements[-1].name == "html"

    def processEOF(self):
        if self.tree.openElements[-1].name == "html":
            assert self.parser.innerHTML
            return
        else:
            ignoreEndTag = self.ignoreEndTagColgroup()
            self.endTagColgroup("colgroup")
            if not ignoreEndTag:
                self.parser.phase.processEOF()

    def processCharacters(self, data):
        ignoreEndTag = self.ignoreEndTagColgroup()
        self.endTagColgroup("colgroup")
        if not ignoreEndTag:
            self.parser.phase.processCharacters(data)

    def startTagCol(self, name ,attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagOther(self, name, attributes):
        ignoreEndTag = self.ignoreEndTagColgroup()
        self.endTagColgroup("colgroup")
        if not ignoreEndTag:
            self.parser.phase.processStartTag(name, attributes)

    def endTagColgroup(self, name):
        if self.ignoreEndTagColgroup():
            # innerHTML case
            assert self.parser.innerHTML
            self.parser.parseError()
        else:
            self.tree.openElements.pop()
            self.parser.phase = self.parser.phases["inTable"]

    def endTagCol(self, name):
        self.parser.parseError("no-end-tag", {"name": "col"})

    def endTagOther(self, name):
        ignoreEndTag = self.ignoreEndTagColgroup()
        self.endTagColgroup("colgroup")
        if not ignoreEndTag:
            self.parser.phase.processEndTag(name)


class InTableBodyPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table0
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("tr", self.startTagTr),
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead"),
             self.startTagTableOther)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "td", "th",
              "tr"), self.endTagIgnore)
        ])
        self.endTagHandler.default = self.endTagOther

    # helper methods
    def clearStackToTableBodyContext(self):
        while self.tree.openElements[-1].name not in ("tbody", "tfoot",
          "thead", "html"):
            #self.parser.parseError("unexpected-implied-end-tag-in-table",
            #  {"name": self.tree.openElements[-1].name})
            self.tree.openElements.pop()
        if self.tree.openElements[-1].name == "html":
            assert self.parser.innerHTML

    # the rest
    def processEOF(self):
        self.parser.phases["inTable"].processEOF()
    
    def processSpaceCharacters(self,data):
        self.parser.phases["inTable"].processSpaceCharacters(data)

    def processCharacters(self,data):
        self.parser.phases["inTable"].processCharacters(data)

    def startTagTr(self, name, attributes):
        self.clearStackToTableBodyContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inRow"]

    def startTagTableCell(self, name, attributes):
        self.parser.parseError("unexpected-cell-in-table-body", {"name": name})
        self.startTagTr("tr", {})
        self.parser.phase.processStartTag(name, attributes)

    def startTagTableOther(self, name, attributes):
        # XXX AT Any ideas on how to share this with endTagTable?
        if (self.tree.elementInScope("tbody", True) or
            self.tree.elementInScope("thead", True) or
            self.tree.elementInScope("tfoot", True)):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.tree.openElements[-1].name)
            self.parser.phase.processStartTag(name, attributes)
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        self.parser.phases["inTable"].processStartTag(name, attributes)

    def endTagTableRowGroup(self, name):
        if self.tree.elementInScope(name, True):
            self.clearStackToTableBodyContext()
            self.tree.openElements.pop()
            self.parser.phase = self.parser.phases["inTable"]
        else:
            self.parser.parseError("unexpected-end-tag-in-table-body",
              {"name": name})

    def endTagTable(self, name):
        if (self.tree.elementInScope("tbody", True) or
            self.tree.elementInScope("thead", True) or
            self.tree.elementInScope("tfoot", True)):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.tree.openElements[-1].name)
            self.parser.phase.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError("unexpected-end-tag-in-table-body",
          {"name": name})

    def endTagOther(self, name):
        self.parser.phases["inTable"].processEndTag(name)


class InRowPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-row
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead",
              "tr"), self.startTagTableOther)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("tr", self.endTagTr),
            ("table", self.endTagTable),
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            (("body", "caption", "col", "colgroup", "html", "td", "th"),
              self.endTagIgnore)
        ])
        self.endTagHandler.default = self.endTagOther

    # helper methods (XXX unify this with other table helper methods)
    def clearStackToTableRowContext(self):
        while self.tree.openElements[-1].name not in ("tr", "html"):
            self.parser.parseError("unexpected-implied-end-tag-in-table-row",
              {"name": self.tree.openElements[-1].name})
            self.tree.openElements.pop()

    def ignoreEndTagTr(self):
        return not self.tree.elementInScope("tr", tableVariant=True)

    # the rest
    def processEOF(self):
        self.parser.phases["inTable"].processEOF()
    
    def processSpaceCharacters(self, data):
        self.parser.phases["inTable"].processSpaceCharacters(data)        

    def processCharacters(self, data):
        self.parser.phases["inTable"].processCharacters(data)

    def startTagTableCell(self, name, attributes):
        self.clearStackToTableRowContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inCell"]
        self.tree.activeFormattingElements.append(Marker)

    def startTagTableOther(self, name, attributes):
        ignoreEndTag = self.ignoreEndTagTr()
        self.endTagTr("tr")
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not ignoreEndTag:
            self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.phases["inTable"].processStartTag(name, attributes)

    def endTagTr(self, name):
        if not self.ignoreEndTagTr():
            self.clearStackToTableRowContext()
            self.tree.openElements.pop()
            self.parser.phase = self.parser.phases["inTableBody"]
        else:
            # innerHTML case
            assert self.parser.innerHTML
            self.parser.parseError()

    def endTagTable(self, name):
        ignoreEndTag = self.ignoreEndTagTr()
        self.endTagTr("tr")
        # Reprocess the current tag if the tr end tag was not ignored
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not ignoreEndTag:
            self.parser.phase.processEndTag(name)

    def endTagTableRowGroup(self, name):
        if self.tree.elementInScope(name, True):
            self.endTagTr("tr")
            self.parser.phase.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError("unexpected-end-tag-in-table-row",
            {"name": name})

    def endTagOther(self, name):
        self.parser.phases["inTable"].processEndTag(name)

class InCellPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-cell
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableOther)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            (("td", "th"), self.endTagTableCell),
            (("body", "caption", "col", "colgroup", "html"), self.endTagIgnore),
            (("table", "tbody", "tfoot", "thead", "tr"), self.endTagImply)
        ])
        self.endTagHandler.default = self.endTagOther

    # helper
    def closeCell(self):
        if self.tree.elementInScope("td", True):
            self.endTagTableCell("td")
        elif self.tree.elementInScope("th", True):
            self.endTagTableCell("th")

    # the rest
    def processEOF(self):
        self.parser.phases["inBody"].processEOF()
        
    def processCharacters(self, data):
        self.parser.phases["inBody"].processCharacters(data)

    def startTagTableOther(self, name, attributes):
        if self.tree.elementInScope("td", True) or \
          self.tree.elementInScope("th", True):
            self.closeCell()
            self.parser.phase.processStartTag(name, attributes)
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)
        # Optimize this for subsequent invocations. Can't do this initially
        # because self.phases doesn't really exist at that point.
        self.startTagHandler.default =\
          self.parser.phases["inBody"].processStartTag

    def endTagTableCell(self, name):
        if self.tree.elementInScope(name, True):
            self.tree.generateImpliedEndTags(name)
            if self.tree.openElements[-1].name != name:
                self.parser.parseError("unexpected-cell-end-tag",
                  {"name": name})
                while True:
                    node = self.tree.openElements.pop()
                    if node.name == name:
                        break
            else:
                self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()
            self.parser.phase = self.parser.phases["inRow"]
        else:
            self.parser.parseError("unexpected-end-tag", {"name": name})

    def endTagIgnore(self, name):
        self.parser.parseError("unexpected-end-tag", {"name": name})

    def endTagImply(self, name):
        if self.tree.elementInScope(name, True):
            self.closeCell()
            self.parser.phase.processEndTag(name)
        else:
            # sometimes innerHTML case
            self.parser.parseError()

    def endTagOther(self, name):
        self.parser.phases["inBody"].processEndTag(name)
        # Optimize this for subsequent invocations. Can't do this initially
        # because self.phases doesn't really exist at that point.
        self.endTagHandler.default = self.parser.phases["inBody"].processEndTag


class InSelectPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("option", self.startTagOption),
            ("optgroup", self.startTagOptgroup),
            ("select", self.startTagSelect),
            ("input", self.startTagInput)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("option", self.endTagOption),
            ("optgroup", self.endTagOptgroup),
            ("select", self.endTagSelect),
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td",
              "th"), self.endTagTableElements)
        ])
        self.endTagHandler.default = self.endTagOther

    # http://www.whatwg.org/specs/web-apps/current-work/#in-select
    def processEOF(self):
        if self.tree.openElements[-1].name != "html":
            self.parser.parseError("eof-in-select")
        else:
            assert self.parser.innerHtml

    def processCharacters(self, data):
        self.tree.insertText(data)

    def startTagOption(self, name, attributes):
        # We need to imply </option> if <option> is the current node.
        if self.tree.openElements[-1].name == "option":
            self.tree.openElements.pop()
        self.tree.insertElement(name, attributes)

    def startTagOptgroup(self, name, attributes):
        if self.tree.openElements[-1].name == "option":
            self.tree.openElements.pop()
        if self.tree.openElements[-1].name == "optgroup":
            self.tree.openElements.pop()
        self.tree.insertElement(name, attributes)

    def startTagSelect(self, name, attributes):
        self.parser.parseError("unexpected-select-in-select")
        self.endTagSelect("select")

    def startTagInput(self, name, attributes):
        self.parser.parseError("unexpected-input-in-select")
        self.endTagSelect("select")
        self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-in-select",
          {"name": name})

    def endTagOption(self, name):
        if self.tree.openElements[-1].name == "option":
            self.tree.openElements.pop()
        else:
            self.parser.parseError("unexpected-end-tag-in-select",
              {"name": "option"})

    def endTagOptgroup(self, name):
        # </optgroup> implicitly closes <option>
        if self.tree.openElements[-1].name == "option" and \
          self.tree.openElements[-2].name == "optgroup":
            self.tree.openElements.pop()
        # It also closes </optgroup>
        if self.tree.openElements[-1].name == "optgroup":
            self.tree.openElements.pop()
        # But nothing else
        else:
            self.parser.parseError("unexpected-end-tag-in-select",
              {"name": "optgroup"})

    def endTagSelect(self, name):
        if self.tree.elementInScope("select", True):
            node = self.tree.openElements.pop()
            while node.name != "select":
                node = self.tree.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTableElements(self, name):
        self.parser.parseError("unexpected-end-tag-in-select",
          {"name": name})
        if self.tree.elementInScope(name, True):
            self.endTagSelect("select")
            self.parser.phase.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag-in-select",
          {"name": name})


class InSelectInTablePhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td", "th"), self.startTagTable)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td", "th"), self.endTagTable)
        ])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        self.parser.phases["inSelect"].processEOF()

    def processCharacters(self, data):
        self.parser.phases["inSelect"].processCharacters(data)
    
    def startTagTable(self, name, attributes):
        self.parser.parseError("unexpected-table-element-start-tag-in-select-in-table", {"name": name})
        self.endTagOther("select")
        self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.phases["inSelect"].processStartTag(name, attributes)

    def endTagTable(self, name):
        self.parser.parseError("unexpected-table-element-end-tag-in-select-in-table", {"name": name})
        if self.tree.elementInScope(name):
            self.endTagOther("select")
            self.parser.phase.processEndTag(name)

    def endTagOther(self, name):
        self.parser.phases["inSelect"].processEndTag(name)


class AfterBodyPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
                ("html", self.startTagHtml)
                ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([("html", self.endTagHtml)])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        #Stop parsing
        pass
    
    def processComment(self, data):
        # This is needed because data is to be appended to the <html> element
        # here and not to whatever is currently open.
        self.tree.insertComment(data, self.tree.openElements[0])

    def processCharacters(self, data):
        self.parser.parseError("unexpected-char-after-body")
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processCharacters(data)

    def startTagHtml(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-after-body",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processStartTag(name, attributes)

    def endTagHtml(self,name):
        if self.parser.innerHTML:
            self.parser.parseError("unexpected-end-tag-after-body-innerhtml")
        else:
            self.parser.phase = self.parser.phases["afterAfterBody"]

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag-after-body",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processEndTag(name)

class InFramesetPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-frameset
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("frameset", self.startTagFrameset),
            ("frame", self.startTagFrame),
            ("noframes", self.startTagNoframes)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("frameset", self.endTagFrameset),
            ("noframes", self.endTagNoframes)
        ])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        if self.tree.openElements[-1].name != "html":
            self.parser.parseError("eof-in-frameset")
        else:
            assert self.parser.innerHTML

    def processCharacters(self, data):
        self.parser.parseError("unexpected-char-in-frameset")

    def startTagFrameset(self, name, attributes):
        self.tree.insertElement(name, attributes)

    def startTagFrame(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagNoframes(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-in-frameset",
          {"name": name})

    def endTagFrameset(self, name):
        if self.tree.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError("unexpected-frameset-in-frameset-innerhtml")
        else:
            self.tree.openElements.pop()
        if (not self.parser.innerHTML and
            self.tree.openElements[-1].name != "frameset"):
            # If we're not in innerHTML mode and the the current node is not a
            # "frameset" element (anymore) then switch.
            self.parser.phase = self.parser.phases["afterFrameset"]

    def endTagNoframes(self, name):
        self.parser.phases["inBody"].processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag-in-frameset",
          {"name": name})


class AfterFramesetPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#after3
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("noframes", self.startTagNoframes)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("html", self.endTagHtml)
        ])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        #Stop parsing
        pass

    def processCharacters(self, data):
        self.parser.parseError("unexpected-char-after-frameset")

    def startTagNoframes(self, name, attributes):
        self.parser.phases["inHead"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("unexpected-start-tag-after-frameset",
          {"name": name})

    def endTagHtml(self, name):
        self.parser.phase = self.parser.phases["afterAfterFrameset"]

    def endTagOther(self, name):
        self.parser.parseError("unexpected-end-tag-after-frameset",
          {"name": name})


class AfterAfterBodyPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml)
        ])
        self.startTagHandler.default = self.startTagOther

    def processEOF(self):
        pass

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processSpaceCharacters(self, data):
        self.parser.phases["inBody"].processSpaceCharacters(data)

    def processCharacters(self, data):
        self.parser.parseError("expected-eof-but-got-char")
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processCharacters(data)

    def startTagHtml(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("expected-eof-but-got-start-tag",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError("expected-eof-but-got-end-tag",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processEndTag(name)

class AfterAfterFramesetPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("noframes", self.startTagNoFrames)
        ])
        self.startTagHandler.default = self.startTagOther

    def processEOF(self):
        pass

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processSpaceCharacters(self, data):
        self.parser.phases["inBody"].processSpaceCharacters(data)

    def processCharacters(self, data):
        self.parser.parseError("expected-eof-but-got-char")
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processCharacters(data)

    def startTagHtml(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagNoFrames(self, name, attributes):
        self.parser.phases["inHead"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError("expected-eof-but-got-start-tag",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError("expected-eof-but-got-end-tag",
          {"name": name})
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processEndTag(name)

class ParseError(Exception):
    """Error in parsed document"""
    pass
