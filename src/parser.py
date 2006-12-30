# Differences from the current specification (23 December 2006) are as follows:
# * Phases and insertion modes are one concept in parser.py.
# * EOF handling is slightly different to make sure <html>, <head> and <body>
#   always exist.
# * We also deal with content when there's no DOCTYPE.
# It is expected that the specification will catch up with us in due course ;-)
#
# It should be trivial to add the following cases. However, we should probably
# also look into comment handling and such then...
# * A <p> element end tag creates an empty <p> element when there's no <p>
#   element in scope.
# * A <br> element end tag creates an empty <br> element.

try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

import tokenizer

import treebuilders
from treebuilders.base import Marker
from treebuilders import DOMlite

import utils
from constants import contentModelFlags, spaceCharacters
from constants import scopingElements, formattingElements, specialElements
from constants import headingElements, tableInsertModeElements

class HTMLParser(object):
    """Main parser class"""

    def __init__(self, strict = False, tree=DOMlite.TreeBuilder):
        # Raise an exception on the first error encountered
        self.strict = strict

        self.tree = tree()

        self.phases = {
            "initial": InitialPhase(self, self.tree),
            "rootElement": RootElementPhase(self, self.tree),
            "beforeHead": BeforeHeadPhase(self, self.tree),
            "inHead": InHeadPhase(self, self.tree),
            "afterHead": AfterHeadPhase(self, self.tree),
            "inBody": InBodyPhase(self, self.tree),
            "inTable": InTablePhase(self, self.tree),
            "inCaption": InCaptionPhase(self, self.tree),
            "inColumnGroup": InColumnGroupPhase(self, self.tree),
            "inTableBody": InTableBodyPhase(self, self.tree),
            "inRow": InRowPhase(self, self.tree),
            "inCell": InCellPhase(self, self.tree),
            "inSelect": InSelectPhase(self, self.tree),
            "afterBody": AfterBodyPhase(self, self.tree),
            "inFrameset": InFramesetPhase(self, self.tree),
            "afterFrameset": AfterFramesetPhase(self, self.tree),
            "trailingEnd": TrailingEndPhase(self, self.tree)
        }
        self.phase = self.phases["initial"]
        # We only seem to have InBodyPhase testcases where the following is
        # relevant ... need others too
        self.lastPhase = None

    def parse(self, stream, innerHTML=False):
        """Stream should be a stream of unicode bytes. Character encoding
        issues have not yet been dealt with."""

        # XXX - need to ensure the tree is reset here
        # Why? -- anne

        # We don't actually support innerHTML yet but this should allow
        # assertations
        self.innerHTML = innerHTML

        self.tokenizer = tokenizer.HTMLTokenizer(stream)

        # XXX This is temporary for the moment so there isn't any other
        # changes needed for the parser to work with the iterable tokenizer
        for token in self.tokenizer:
            type = token["type"]
            method = getattr(self.phase, "process%s" % type, None)
            if type in ("Characters", "SpaceCharacters", "Comment"):
                method(token["data"])
            elif type in ("StartTag", "Doctype"):
                method(token["name"], token["data"])
            elif type == "EndTag":
                method(token["name"])
            elif type == "ParseError":
                self.parseError()
            else:
                self.atheistParseError()

        # When the loop finishes it's EOF
        self.phase.processEOF()

        return self.tree.getDocument()

    def parseError(self):
        if self.strict:
            raise ParseError

    def atheistParseError(self):
        """This error is not an error"""
        pass

    #XXX - almost everthing after this point should be moved into a
    #seperate treebuilder object


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
            if node == self.tree.openElements[0]:
                last = True
                if node.name not in ['td', 'th']:
                    # XXX
                    assert self.innerHTML
                    raise NotImplementedError
            # Check for conditions that should only happen in the innerHTML
            # case
            if node.name in ("select", "colgroup", "head", "frameset"):
                # XXX
                assert self.innerHTML
            if node.name in newModes:
                self.phase = self.phases[newModes[node.name]]
                break
            elif node.name == "html":
                if self.tree.headPointer is None:
                    self.phase = self.phases["beforeHead"]
                else:
                   self.phase = self.phases["afterHead"]
                break
            elif last:
                self.phase = self.phases["body"]
                break

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
        self.tree.generateImpliedEndTags()
        if self.parser.innerHTML == False\
          or len(self.tree.openElements) > 1:
            # XXX No need to check for "body" because our EOF handling is not
            # per specification. (Specification needs an update.)
            self.parser.parseError()
        # Stop parsing

    def processComment(self, data):
        # For most phases the following is correct. Where it's not it will be
        # overridden.
        self.tree.insertComment(data, self.tree.openElements[-1])

    def processDoctype(self, name, error):
        self.parser.parseError()

    def processSpaceCharacters(self, data):
        self.tree.insertText(data)

    def processStartTag(self, name, attributes):
        self.startTagHandler[name](name, attributes)

    def startTagHtml(self, name, attributes):
        # XXX Need a check here to see if the first start tag token emitted is
        # this token... If it's not, invoke self.parser.parseError().
        for attr, value in attributes.iteritems():
            if attr not in self.tree.openElements[0].attributes:
                self.tree.openElements[0].attributes[attr] = value

    def processEndTag(self, name):
        self.endTagHandler[name](name)


class InitialPhase(Phase):
    # This phase deals with error handling as well which is currently not
    # covered in the specification. The error handling is typically known as
    # "quirks mode". It is expected that a future version of HTML5 will defin
    # this.
    #
    # AT Given that. I think it should be possible to merge this phase with the
    # root element phase in due course.
    def processEOF(self):
        self.parser.phase = self.parser.phases["rootElement"]
        self.parser.phase.processEOF()

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processDoctype(self, name, error):
        self.tree.insertDoctype(name)
        self.parser.phase = self.parser.phases["rootElement"]

    def processSpaceCharacters(self, data):
        self.tree.insertText(data, self.tree.document)

    def processCharacters(self, data):
        self.parser.parseError()
        self.parser.phase = self.parser.phases["rootElement"]
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.phase = self.parser.phases["rootElement"]
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.phase = self.parser.phases["rootElement"]
        self.parser.phase.processEndTag(name)


class RootElementPhase(Phase):
    # helper methods
    def insertHtmlElement(self):
        element = self.tree.createElement("html", {})
        self.tree.openElements.append(element)
        self.tree.document.appendChild(element)
        self.parser.phase = self.parser.phases["beforeHead"]

    # other
    def processEOF(self):
        self.insertHtmlElement()
        self.parser.phase.processEOF()

    def processComment(self, data):
        self.tree.insertComment(data, self.tree.document)

    def processSpaceCharacters(self, data):
        self.tree.insertText(data, self.tree.document)

    def processCharacters(self, data):
        self.insertHtmlElement()
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
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
            ("html", self.endTagHtml)
        ])
        self.endTagHandler.default = self.endTagOther

    def processEOF(self):
        self.startTagHead("head", {})
        self.parser.phase.processEOF()

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

    def endTagHtml(self, name):
        self.startTagHead("head", {})
        self.parser.phase.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError()

class InHeadPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler =  utils.MethodDispatcher([
            ("html", self.startTagHtml),
            (("title", "style"), self.startTagTitleStyle),
            ("script", self.startTagScript),
            (("base", "link", "meta"), self.startTagBaseLinkMeta),
            ("head", self.startTagHead)
        ])
        self.startTagHandler.default = self.startTagOther

        self. endTagHandler = utils.MethodDispatcher([
            ("head", self.endTagHead),
            ("html", self.endTagHtml),
            (("title", "style", "script"), self.endTagTitleStyleScript)
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
    def processEOF(self):
        if self.tree.openElements[-1].name in ("title", "style", "script"):
            self.tree.openElements.pop()
        self.anythingElse()
        self.parser.phase.processEOF()

    def processCharacters(self, data):
        if self.tree.openElements[-1].name in ("title", "style", "script"):
            self.tree.insertText(data)
        else:
            self.anythingElse()
            self.parser.phase.processCharacters(data)

    def startTagHead(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.headPointer = self.tree.openElements[-1]
        self.parser.phase = self.parser.phases["inHead"]

    def startTagTitleStyle(self, name, attributes):
        cmFlags = {"title":"RCDATA", "style":"CDATA"}
        element = self.tree.createElement(name, attributes)
        self.appendToHead(element)
        self.tree.openElements.append(element)
        self.parser.tokenizer.contentModelFlag =\
          contentModelFlags[cmFlags[name]]

    def startTagScript(self, name, attributes):
        element = self.tree.createElement(name, attributes)
        element._flags.append("parser-inserted")

        # XXX in theory we should check if we're actually in the InHead state
        # here and if the headElementPointer is not zero but it seems to work
        # without that being the case.
        self.tree.openElements[-1].appendChild(element)
        self.tree.openElements.append(element)

        # XXX AT we could use self.tree.insertElement(name, attributes) ...
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagBaseLinkMeta(self, name, attributes):
        element = self.tree.createElement(name, attributes)
        self.appendToHead(element)

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.phase.processStartTag(name, attributes)

    def endTagHead(self, name):
        if self.tree.openElements[-1].name == "head":
            self.tree.openElements.pop()
        else:
            self.parser.parseError()
        self.parser.phase = self.parser.phases["afterHead"]

    def endTagHtml(self, name):
        self.anythingElse()
        self.parser.phase.processEndTag(name)

    def endTagTitleStyleScript(self, name):
        if self.tree.openElements[-1].name == name:
            self.tree.openElements.pop()
        else:
            self.parser.parseError()

    def endTagOther(self, name):
        self.parser.parseError()

    def anythingElse(self):
        if self.tree.openElements[-1].name == "head":
            self.endTagHead("head")
        else:
            self.parser.phase = self.parser.phases["afterHead"]

class AfterHeadPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("body", self.startTagBody),
            ("frameset", self.startTagFrameset),
            (("base", "link", "meta", "script", "style", "title"),
              self.startTagFromHead)
        ])
        self.startTagHandler.default = self.startTagOther

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
        self.parser.parseError()
        self.parser.phase = self.parser.phases["inHead"]
        self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.anythingElse()
        self.parser.phase.processEndTag(name)

    def anythingElse(self):
        self.tree.insertElement("body", {})
        self.parser.phase = self.parser.phases["inBody"]


class InBodyPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-body
    # the crazy mode
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("script", self.startTagScript),
            (("base", "link", "meta", "style", "title"),
              self.startTagFromHead),
            ("body", self.startTagBody),
            (("address", "blockquote", "center", "dir", "div", "dl",
              "fieldset", "listing", "menu", "ol", "p", "pre", "ul"),
              self.startTagCloseP),
            ("form", self.startTagForm),
            (("li", "dd", "dt"), self.startTagListItem),
            ("plaintext",self.startTagPlaintext),
            (headingElements, self.startTagHeading),
            ("a", self.startTagA),
            (("b", "big", "em", "font", "i", "nobr", "s", "small", "strike",
              "strong", "tt", "u"),self.startTagFormatting),
            ("button", self.startTagButton),
            (("marquee", "object"), self.startTagMarqueeObject),
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
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
              "tr"), self.startTagMisplaced),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.startTagNew)
        ])
        self.startTagHandler.default = self.startTagOther

        self.endTagHandler = utils.MethodDispatcher([
            ("p",self.endTagP),
            ("body",self.endTagBody),
            ("html",self.endTagHtml),
            (("address", "blockquote", "center", "div", "dl", "fieldset",
              "listing", "menu", "ol", "pre", "ul"), self.endTagBlock),
            ("form", self.endTagForm),
            (("dd", "dt", "li"), self.endTagListItem),
            (headingElements, self.endTagHeading),
            (("a", "b", "big", "em", "font", "i", "nobr", "s", "small",
              "strike", "strong", "tt", "u"), self.endTagFormatting),
            (("marquee", "object", "button"), self.endTagButtonMarqueeObject),
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
              "tr", "area", "basefont", "bgsound", "br", "embed", "hr",
              "image", "img", "input", "isindex", "param", "select", "spacer",
              "table",  "wbr"),self.endTagMisplacedNone),
            (("noframes", "noscript", "noembed", "textarea", "xmp", "iframe"),
              self.endTagCdataTextAreaXmp),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.endTagNew)
            ])
        self.endTagHandler.default = self.endTagOther

    # helper
    def addFormattingElement(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.activeFormattingElements.append(
            self.tree.openElements[-1])

    # the real deal
    def processCharacters(self, data):
        # XXX The specification says to do this for every character at the
        # moment, but apparently that doesn't match the real world so we don't
        # do it for space characters.
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertText(data)

    def startTagScript(self, name, attributes):
        self.parser.phases["inHead"].processStartTag(name, attributes)

    def startTagFromHead(self, name, attributes):
        self.parser.parseError()
        self.parser.phases["inHead"].processStartTag(name, attributes)

    def startTagBody(self, name, attributes):
        self.parser.parseError()
        if len(self.tree.openElements) == 1 \
          or self.tree.openElements[1].name != "body":
            assert self.parser.innerHTML
        else:
            for attr, value in attributes.iteritems():
                if attr not in self.tree.openElements[1].attributes:
                    self.tree.openElements[1].attributes[attr] = value

    def startTagCloseP(self, name, attributes):
        if self.tree.elementInScope("p"):
            self.endTagP("p")
        self.tree.insertElement(name, attributes)

    def startTagForm(self, name, attributes):
        if self.tree.formPointer:
            self.parser.parseError()
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
                for j in range(i+1):
                    self.tree.openElements.pop()
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
        for item in headingElements:
            if self.tree.elementInScope(item):
                self.parser.parseError()
                item = self.tree.openElements.pop()
                while item.name not in headingElements:
                    item = self.tree.openElements.pop()
                break
        self.tree.insertElement(name, attributes)

    def startTagA(self, name, attributes):
        afeAElement = self.tree.elementInActiveFormattingElements("a")
        if afeAElement:
            self.parser.parseError()
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

    def startTagButton(self, name, attributes):
        if self.tree.elementInScope("button"):
            self.parser.parseError()
            self.processEndTag("button")
            self.parser.phase.processStartTag(name, attributes)
        else:
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(name, attributes)
            self.tree.activeFormattingElements.append(Marker)

    def startTagMarqueeObject(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        self.tree.activeFormattingElements.append(Marker)

    def startTagXmp(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

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
        self.parser.parseError()
        self.processStartTag("img", attributes)

    def startTagInput(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        if self.tree.formPointer:
            # XXX Not exactly sure what to do here
            self.tree.openElements[-1].form = self.tree.formPointer
        self.tree.openElements.pop()

    def startTagIsIndex(self, name, attributes):
        self.parser.parseError()
        if self.tree.formPointer:
            return
        self.processStartTag("form", {})
        self.processStartTag("hr", {})
        self.processStartTag("p", {})
        self.processStartTag("label", {})
        # XXX Localization ...
        self.processCharacters(
            "This is a searchable index. Insert your search keywords here:")
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

    def startTagCdata(self, name, attributes):
        """iframe, noembed noframes, noscript(if scripting enabled)"""
        self.tree.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagSelect(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inSelect"]

    def startTagMisplaced(self, name, attributes):
        """ Elements that should be children of other elements that have a
        different insertion mode; here they are ignored
        "caption", "col", "colgroup", "frame", "frameset", "head",
        "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
        "tr", "noscript"
        """
        self.parser.parseError()

    def startTagNew(self, name, other):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

    def startTagOther(self, name, attributes):
        self.tree.reconstructActiveFormattingElements()
        self.tree.insertElement(name, attributes)

    def endTagP(self, name):
        self.tree.generateImpliedEndTags("p")
        if self.tree.openElements[-1].name != "p":
            self.parser.parseError()
        while self.tree.elementInScope("p"):
            self.tree.openElements.pop()

    def endTagBody(self, name):
        if self.tree.openElements[1].name != "body":
            # innerHTML case
            self.parser.parseError()
            return
        if self.tree.openElements[-1].name != "body":
            self.parser.parseError()
        self.parser.phase = self.parser.phases["afterBody"]

    def endTagHtml(self, name):
        self.endTagBody(name)
        if not self.parser.innerHTML:
            self.parser.phase.processEndTag(name)

    def endTagBlock(self, name):
        inScope = self.tree.elementInScope(name)
        if inScope:
            self.tree.generateImpliedEndTags()
        if self.tree.openElements[-1].name != name:
             self.parser.parseError()
        if inScope:
            node = self.tree.openElements.pop()
            while node.name != name:
                node = self.tree.openElements.pop()

    def endTagForm(self, name):
        self.endTagBlock(name)
        self.tree.formPointer = None

    def endTagListItem(self, name):
        # AT Could merge this with the Block case
        if self.tree.elementInScope(name):
            self.tree.generateImpliedEndTags(name)
            if self.tree.openElements[-1].name != name:
                self.parser.parseError()

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
            self.parser.parseError()

        for item in headingElements:
            if self.tree.elementInScope(item):
                item = self.tree.openElements.pop()
                while item.name not in headingElements:
                    item = self.tree.openElements.pop()
                break

    def endTagFormatting(self, name):
        """The much-feared adoption agency algorithm
        """
        while True:
            # Step 1 paragraph 1
            afeElement = self.tree.elementInActiveFormattingElements(name)
            if not afeElement or (afeElement in self.tree.openElements and
              not self.tree.elementInScope(afeElement.name)):
                self.parser.parseError()
                return

            # Step 1 paragraph 2
            elif afeElement not in self.tree.openElements:
                self.parser.parseError()
                self.tree.activeFormattingElements.remove(afeElement)
                return

            # Step 1 paragraph 3
            if afeElement != self.tree.openElements[-1]:
                self.parser.parseError()

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
                    # XXX should this be index(node) or index(node)+1
                    # Anne: I think +1 is ok. Given x = [2,3,4,5]
                    # x.index(3) gives 1 and then x[1 +1] gives 4...
                    bookmark = self.tree.activeFormattingElements.\
                      index(node) + 1
                # Step 7.5
                if node.childNodes:
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
            clone.childNodes.extend(furthestBlock.childNodes)
            furthestBlock.childNodes = []

            # Step 11
            furthestBlock.childNodes.append(clone)

            # Step 12
            self.tree.activeFormattingElements.remove(afeElement)
            self.tree.activeFormattingElements.insert(bookmark, clone)

            # Step 13
            self.tree.openElements.remove(afeElement)
            self.tree.openElements.insert(
              self.tree.openElements.index(furthestBlock) + 1, clone)

    def endTagButtonMarqueeObject(self, name):
        if self.tree.elementInScope(name):
            self.tree.generateImpliedEndTags()
        if self.tree.openElements[-1].name != name:
            self.parser.parseError()

        if self.tree.elementInScope(name):
            element = self.tree.openElements.pop()
            while element.name != name:
                element = self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()

    def endTagMisplacedNone(self, name):
        """ Elements that should be children of other elements that have a
        different insertion mode or elements that have no end tag;
        here they are ignored
        "caption", "col", "colgroup", "frame", "frameset", "head",
        "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
        "tr", "noscript, "area", "basefont", "bgsound", "br", "embed",
        "hr", "iframe", "image", "img", "input", "isindex", "noembed",
        "noframes", "param", "select", "spacer", "table", "textarea", "wbr""
        """
        self.parser.parseError()

    def endTagCdataTextAreaXmp(self, name):
        if self.tree.openElements[-1].name == name:
            self.tree.openElements.pop()
        else:
            self.parser.parseError()

    def endTagNew(self, name):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

    def endTagOther(self, name):
        # XXX This logic should be moved into the treebuilder
        # AT should use reversed instead of [::-1] when Python 2.4 == True.
        for node in self.tree.openElements[::-1]:
            if node.name == name:
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != name:
                    self.parser.parseError()
                while self.tree.openElements.pop() != node:
                    pass
                break
            else:
                if node.name in specialElements | scopingElements:
                    self.parser.parseError()
                    break

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
            ("table", self.startTagTable)
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
            self.tree.openElements.pop()
            self.parser.parseError()
        # When the current node is <html> it's an innerHTML case

    # processing methods
    def processCharacters(self, data):
        self.parser.parseError()
        # Make all the special element rearranging voodoo kick in
        self.tree.insertFromTable = True
        # Process the character in the "in body" mode
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
        self.parser.parseError()
        self.parser.phase.processEndTag("table")
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError()
        # Make all the special element rearranging voodoo kick in
        self.tree.insertFromTable = True
        # Process the start tag in the "in body" mode
        self.parser.phases["inBody"].processStartTag(name, attributes)
        self.tree.insertFromTable = False

    def endTagTable(self, name):
        if self.tree.elementInScope("table", True):
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name == "table":
                self.parser.parseError()
            while self.tree.openElements[-1].name != "table":
                self.tree.openElements.pop()
            self.tree.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            self.parser.parseError()
            # innerHTML case

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        # Make all the special element rearranging voodoo kick in
        self.parser.insertFromTable = True
        # Process the end tag in the "in body" mode
        self.parser.phases["inBody"].processEndTag(name)
        self.parser.insertFromTable = False


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

    def processCharacters(self, data):
        self.parser.phases["inBody"].processCharacters(data)

    def startTagTableElement(self, name, attributes):
        self.parser.parseError()
        self.parser.phase.processEndTag("caption")
        # XXX how do we know the tag is _always_ ignored in the innerHTML
        # case and therefore shouldn't be processed again? I'm not sure this
        # strategy makes sense...
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def endTagCaption(self, name):
        if self.tree.elementInScope(name, True):
            # AT this code is quite similar to endTagTable in "InTable"
            self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name == "caption":
                self.parser.parseError()
            while self.tree.openElements[-1].name != "caption":
                self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()
            self.parser.phase = self.parser.phases["inTable"]
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTable(self, name):
        self.parser.parseError()
        self.parser.phase.processEndTag("caption")
        # XXX ...
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def endTagIgnore(self, name):
        self.parser.parseError()

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

    def processCharacters(self, data):
        self.endTagColgroup("colgroup")
        # XXX
        if not self.parser.innerHTML:
            self.parser.phase.processCharacters(data)

    def startTagCol(self, name ,attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagOther(self, name, attributes):
        self.endTagColgroup("colgroup")
        # XXX how can be sure it's always ignored?
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def endTagColgroup(self, name):
        if self.tree.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError()
        else:
            self.tree.openElements.pop()
            self.parser.phase = self.parser.phases["inTable"]

    def endTagCol(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        self.endTagColgroup("colgroup")
        # XXX how can be sure it's always ignored?
        if not self.parser.innerHTML:
            self.parser.phase.processEndTag(name)


class InTableBodyPhase(Phase):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table0
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)
        self.startTagHandler = utils.MethodDispatcher([
            ("html", self.startTagHtml),
            ("tr", self.startTagTr),
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead"), self.startTagTableOther)
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
            self.tree.openElements.pop()
            self.parser.parseError()

    # the rest
    def processCharacters(self,data):
        self.parser.phases["inTable"].processCharacters(data)

    def startTagTr(self, name, attributes):
        self.clearStackToTableBodyContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inRow"]

    def startTagTableCell(self, name, attributes):
        self.parser.parseError()
        self.startTagTr("tr", {})
        self.parser.phase.processStartTag(name, attributes)

    def startTagTableOther(self, name, attributes):
        # XXX AT Any ideas on how to share this with endTagTable?
        if self.tree.elementInScope("tbody", True) or \
          self.tree.elementInScope("thead", True) or \
          self.tree.elementInScope("tfoot", True):
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
            self.parser.parseError()

    def endTagTable(self, name):
        if self.tree.elementInScope("tbody", True) or \
          self.tree.elementInScope("thead", True) or \
          self.tree.elementInScope("tfoot", True):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.tree.openElements[-1].name)
            self.parser.phase.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

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
            self.tree.openElements.pop()
            self.parser.parseError()

    # the rest
    def processCharacters(self, data):
        self.parser.phases["inTable"].processCharacters(data)

    def startTagTableCell(self, name, attributes):
        self.clearStackToTableRowContext()
        self.tree.insertElement(name, attributes)
        self.parser.phase = self.parser.phases["inCell"]
        self.tree.activeFormattingElements.append(Marker)

    def startTagTableOther(self, name, attributes):
        self.endTagTr("tr")
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not self.parser.innerHTML:
            self.parser.phase.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.phases["inTable"].processStartTag(name, attributes)

    def endTagTr(self, name):
        if self.tree.elementInScope("tr", True):
            self.clearStackToTableRowContext()
            self.tree.openElements.pop()
            self.parser.phase = self.parser.phases["inTableBody"]
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTable(self, name):
        self.endTagTr("tr")
        # Reprocess the current tag if the tr end tag was not ignored
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not self.parser.innerHTML:
            self.parser.phase.processEndTag(name)

    def endTagTableRowGroup(self, name):
        if self.tree.elementInScope(name, True):
            self.endTagTr("tr")
            self.parser.phase.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

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
                self.parser.parseError()
                while True:
                    node = self.tree.openElements.pop()
                    if node.name == name:
                        break
            else:
                self.tree.openElements.pop()
            self.tree.clearActiveFormattingElements()
            self.parser.phase = self.parser.phases["inRow"]
        else:
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

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
            ("select", self.startTagSelect)
        ])
        self.startTagHandler.default = self.processAnythingElse

        self.endTagHandler = utils.MethodDispatcher([
            ("option", self.endTagOption),
            ("optgroup", self.endTagOptgroup),
            ("select", self.endTagSelect),
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td",
              "th"), self.endTagTableElements)
        ])
        self.endTagHandler.default = self.processAnythingElse

    # http://www.whatwg.org/specs/web-apps/current-work/#in-select
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
        self.parser.parseError()
        self.endTagSelect("select")

    def endTagOption(self, name):
        if self.tree.openElements[-1].name == "option":
            self.tree.openElements.pop()
        else:
            self.parser.parseError()

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
            self.parser.parseError()

    def endTagSelect(self, name):
        if self.tree.elementInScope(name, True):
            node = self.tree.openElements.pop()
            while node.name != "select":
                node = self.tree.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTableElements(self, name):
        self.parser.parseError()
        if self.tree.elementInScope(name, True):
            self.endTagSelect()
            self.parser.phase.processEndTag(name)

    def processAnythingElse(self, name, attributes={}):
        self.parser.parseError()


class AfterBodyPhase(Phase):
    def __init__(self, parser, tree):
        Phase.__init__(self, parser, tree)

        # XXX We should prolly add a handler for "html" here as well...
        self.endTagHandler = utils.MethodDispatcher([("html", self.endTagHtml)])
        self.endTagHandler.default = self.endTagOther

    def processComment(self, data):
        # This is needed because data is to be appended to the <html> element
        # here and not to whatever is currently open.
        self.tree.insertComment(data, self.tree.openElements[0])

    def processCharacters(self, data):
        self.parser.parseError()
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.phase = self.parser.phases["inBody"]
        self.parser.phase.processStartTag(name, attributes)

    def endTagHtml(self,name):
        if self.parser.innerHTML:
            self.parser.parseError()
        else:
            self.parser.lastPhase = self.parser.phase
            self.parser.phase = self.parser.phases["trailingEnd"]

    def endTagOther(self, name):
        self.parser.parseError()
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
        self.startTagHandler.default = self.tagOther

        self.endTagHandler = utils.MethodDispatcher([("frameset", self.endTagFrameset)])
        self.endTagHandler.default = self.tagOther

    def processCharacters(self, data):
        self.parser.parseError()

    def startTagFrameset(self, name, attributes):
        self.tree.insertElement(name, attributes)

    def startTagFrame(self, name, attributes):
        self.tree.insertElement(name, attributes)
        self.tree.openElements.pop()

    def startTagNoframes(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def endTagFrameset(self, name):
        if self.tree.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError()
        else:
            self.tree.openElements.pop()
        if not self.parser.innerHTML and \
          self.tree.openElements[-1].name == "frameset":
            self.parser.phase = self.parser.phases["afterFrameset"]

    def tagOther(self, name, attributes={}):
        self.parser.parseError()


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

    def processCharacters(self, data):
        self.parser.parseError()

    def startTagNoframes(self, name, attributes):
        self.parser.phases["inBody"].processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError()

    def endTagHtml(self, name):
        self.parser.lastPhase = self.parser.phase
        self.parser.phase = self.parser.phases["trailingEnd"]

    def endTagOther(self, name):
        self.parser.parseError()


class TrailingEndPhase(Phase):
    def processEOF(self):
        pass

    def processComment(self, data):
        self.parser.insertCommenr(data, self.tree.document)

    def processSpaceCharacters(self, data):
        self.parser.lastPhase.processCharacters(data)

    def processCharacters(self, data):
        self.parser.parseError()
        self.parser.phase = self.parser.lastPhase
        self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.phase = self.parser.lastPhase
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError()
        self.parser.phase = self.parser.lastPhase
        self.parser.phase.processEndTag(name)


class ParseError(Exception):
    """Error in parsed document"""
    pass
