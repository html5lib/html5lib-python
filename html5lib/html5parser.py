from __future__ import absolute_import
from itertools import izip
try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

try:
    any
except:
    # Implement 'any' for python 2.4 and previous
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False
    any.func_annotations = {}
        
try:
    u"abc".startswith((u"a", u"b"))
    def startswithany(unicode, prefixes):
        return unicode.startswith(prefixes)
    startswithany.func_annotations = {}
except:
    # Python 2.4 doesn't accept a tuple as argument to string startswith
    def startswithany(unicode, prefixes):
        for prefix in prefixes:
            if unicode.startswith(prefix):
                return True
        return False
    startswithany.func_annotations = {}

import sys
import types

from . import inputstream
from . import tokenizer

from . import treebuilders
from .treebuilders._base import Marker
from .treebuilders import simpletree

from . import utils
from . import constants
from .constants import spaceCharacters, asciiUpper2Lower
from .constants import formattingElements, specialElements
from .constants import headingElements, tableInsertModeElements
from .constants import cdataElements, rcdataElements, voidElements
from .constants import tokenTypes, ReparseException, namespaces, spaceCharacters
from .constants import htmlIntegrationPointElements, mathmlTextIntegrationPointElements

def parse(doc, treebuilder=u"simpletree", encoding=None,
          namespaceHTMLElements=True):
    u"""Parse a string or file-like object into a tree"""
    tb = treebuilders.getTreeBuilder(treebuilder)
    p = HTMLParser(tb, namespaceHTMLElements=namespaceHTMLElements)
    return p.parse(doc, encoding=encoding)
parse.func_annotations = {}

def parseFragment(doc, container=u"div", treebuilder=u"simpletree", encoding=None, 
                  namespaceHTMLElements=True):
    tb = treebuilders.getTreeBuilder(treebuilder)
    p = HTMLParser(tb, namespaceHTMLElements=namespaceHTMLElements)
    return p.parseFragment(doc, container=container, encoding=encoding)
parseFragment.func_annotations = {}

def method_decorator_metaclass(function):
    class Decorated(type):
        def __new__(meta, classname, bases, classDict):
            for attributeName, attribute in classDict.items():
                if type(attribute) == types.FunctionType:
                    attribute = function(attribute)

                classDict[attributeName] = attribute
            return  type.__new__(meta, classname, bases, classDict)
        __new__.func_annotations = {}
    return Decorated
method_decorator_metaclass.func_annotations = {}

class HTMLParser(object):
    u"""HTML parser. Generates a tree structure from a stream of (possibly
        malformed) HTML"""

    def __init__(self, tree = simpletree.TreeBuilder,
                 tokenizer = tokenizer.HTMLTokenizer, strict = False,
                 namespaceHTMLElements = True, debug=False):
        u"""
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

        self.tree = tree(namespaceHTMLElements)
        self.tokenizer_class = tokenizer
        self.errors = []

        self.phases = dict([(name, cls(self, self.tree)) for name, cls in
                            getPhases(debug).items()])
    __init__.func_annotations = {}

    def _parse(self, stream, innerHTML=False, container=u"div",
               encoding=None, parseMeta=True, useChardet=True, **kwargs):

        self.innerHTMLMode = innerHTML
        self.container = container
        self.tokenizer = self.tokenizer_class(stream, encoding=encoding,
                                              parseMeta=parseMeta,
                                              useChardet=useChardet, 
                                              parser=self, **kwargs)
        self.reset()

        while True:
            try:
                self.mainLoop()
                break
            except ReparseException, e:
                self.reset()
    _parse.func_annotations = {}

    def reset(self):
        self.tree.reset()
        self.firstStartTag = False
        self.errors = []
        self.log = [] #only used with debug mode
        # "quirks" / "limited quirks" / "no quirks"
        self.compatMode = u"no quirks"

        if self.innerHTMLMode:
            self.innerHTML = self.container.lower()

            if self.innerHTML in cdataElements:
                self.tokenizer.state = self.tokenizer.rcdataState
            elif self.innerHTML in rcdataElements:
                self.tokenizer.state = self.tokenizer.rawtextState
            elif self.innerHTML == u'plaintext':
                self.tokenizer.state = self.tokenizer.plaintextState
            else:
                # state already is data state
                # self.tokenizer.state = self.tokenizer.dataState
                pass
            self.phase = self.phases[u"beforeHtml"]
            self.phase.insertHtmlElement()
            self.resetInsertionMode()
        else:
            self.innerHTML = False
            self.phase = self.phases[u"initial"]

        self.lastPhase = None

        self.beforeRCDataPhase = None

        self.framesetOK = True
    reset.func_annotations = {}

    def isHTMLIntegrationPoint(self, element):
        if (element.name == u"annotation-xml" and 
            element.namespace == namespaces[u"mathml"]):
            return (u"encoding" in element.attributes and
                    element.attributes[u"encoding"].translate(
                        asciiUpper2Lower) in 
                    (u"text/html", u"application/xhtml+xml"))
        else:
            return (element.namespace, element.name) in htmlIntegrationPointElements
    isHTMLIntegrationPoint.func_annotations = {}

    def isMathMLTextIntegrationPoint(self, element):
        return (element.namespace, element.name) in mathmlTextIntegrationPointElements
    isMathMLTextIntegrationPoint.func_annotations = {}
        
    def mainLoop(self):
        CharactersToken = tokenTypes[u"Characters"]
        SpaceCharactersToken = tokenTypes[u"SpaceCharacters"]
        StartTagToken = tokenTypes[u"StartTag"]
        EndTagToken = tokenTypes[u"EndTag"]
        CommentToken = tokenTypes[u"Comment"]
        DoctypeToken = tokenTypes[u"Doctype"]
        ParseErrorToken = tokenTypes[u"ParseError"]
        
        for token in self.normalizedTokens():
            new_token = token
            while new_token is not None:
                currentNode = self.tree.openElements[-1] if self.tree.openElements else None
                currentNodeNamespace = currentNode.namespace if currentNode else None
                currentNodeName = currentNode.name if currentNode else None

                type = new_token[u"type"]
                
                if type == ParseErrorToken:
                    self.parseError(new_token[u"data"], new_token.get(u"datavars", {}))
                    new_token = None
                else:
                    if (len(self.tree.openElements) == 0 or
                        currentNodeNamespace == self.tree.defaultNamespace or
                        (self.isMathMLTextIntegrationPoint(currentNode) and
                         ((type == StartTagToken and
                           token[u"name"] not in frozenset([u"mglyph", u"malignmark"])) or
                         type in (CharactersToken, SpaceCharactersToken))) or
                        (currentNodeNamespace == namespaces[u"mathml"] and
                         currentNodeName == u"annotation-xml" and
                         token[u"name"] == u"svg") or
                        (self.isHTMLIntegrationPoint(currentNode) and
                         type in (StartTagToken, CharactersToken, SpaceCharactersToken))):
                        phase = self.phase
                    else:
                        phase = self.phases[u"inForeignContent"]

                    if type == CharactersToken:
                        new_token = phase.processCharacters(new_token)
                    elif type == SpaceCharactersToken:
                         new_token= phase.processSpaceCharacters(new_token)
                    elif type == StartTagToken:
                        new_token = phase.processStartTag(new_token)
                    elif type == EndTagToken:
                        new_token = phase.processEndTag(new_token)
                    elif type == CommentToken:
                        new_token = phase.processComment(new_token)
                    elif type == DoctypeToken:
                        new_token = phase.processDoctype(new_token)

            if (type == StartTagToken and token[u"selfClosing"]
                and not token[u"selfClosingAcknowledged"]):
                self.parseError(u"non-void-element-with-trailing-solidus",
                                {u"name":token[u"name"]})


        # When the loop finishes it's EOF
        reprocess = True
        phases = []
        while reprocess:
            phases.append(self.phase)
            reprocess = self.phase.processEOF()
            if reprocess:
                assert self.phase not in phases
    mainLoop.func_annotations = {}

    def normalizedTokens(self):
        for token in self.tokenizer:
            yield self.normalizeToken(token)
    normalizedTokens.func_annotations = {}

    def parse(self, stream, encoding=None, parseMeta=True, useChardet=True):
        u"""Parse a HTML document into a well-formed tree

        stream - a filelike object or string containing the HTML to be parsed

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        self._parse(stream, innerHTML=False, encoding=encoding, 
                    parseMeta=parseMeta, useChardet=useChardet)
        return self.tree.getDocument()
    parse.func_annotations = {}
    
    def parseFragment(self, stream, container=u"div", encoding=None,
                      parseMeta=False, useChardet=True):
        u"""Parse a HTML fragment into a well-formed tree fragment
        
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
    parseFragment.func_annotations = {}

    def parseError(self, errorcode=u"XXX-undefined-error", datavars={}):
        # XXX The idea is to make errorcode mandatory.
        self.errors.append((self.tokenizer.stream.position(), errorcode, datavars))
        if self.strict:
            raise ParseError
    parseError.func_annotations = {}

    def normalizeToken(self, token):
        u""" HTML5 specific normalizations to the token stream """

        if token[u"type"] == tokenTypes[u"StartTag"]:
            token[u"data"] = dict(token[u"data"][::-1])

        return token
    normalizeToken.func_annotations = {}

    def adjustMathMLAttributes(self, token):
        replacements = {u"definitionurl":u"definitionURL"}
        for k,v in replacements.items():
            if k in token[u"data"]:
                token[u"data"][v] = token[u"data"][k]
                del token[u"data"][k]
    adjustMathMLAttributes.func_annotations = {}

    def adjustSVGAttributes(self, token):
        replacements = {
            u"attributename":u"attributeName",
            u"attributetype":u"attributeType",
            u"basefrequency":u"baseFrequency",
            u"baseprofile":u"baseProfile",
            u"calcmode":u"calcMode",
            u"clippathunits":u"clipPathUnits",
            u"contentscripttype":u"contentScriptType",
            u"contentstyletype":u"contentStyleType",
            u"diffuseconstant":u"diffuseConstant",
            u"edgemode":u"edgeMode",
            u"externalresourcesrequired":u"externalResourcesRequired",
            u"filterres":u"filterRes",
            u"filterunits":u"filterUnits",
            u"glyphref":u"glyphRef",
            u"gradienttransform":u"gradientTransform",
            u"gradientunits":u"gradientUnits",
            u"kernelmatrix":u"kernelMatrix",
            u"kernelunitlength":u"kernelUnitLength",
            u"keypoints":u"keyPoints",
            u"keysplines":u"keySplines",
            u"keytimes":u"keyTimes",
            u"lengthadjust":u"lengthAdjust",
            u"limitingconeangle":u"limitingConeAngle",
            u"markerheight":u"markerHeight",
            u"markerunits":u"markerUnits",
            u"markerwidth":u"markerWidth",
            u"maskcontentunits":u"maskContentUnits",
            u"maskunits":u"maskUnits",
            u"numoctaves":u"numOctaves",
            u"pathlength":u"pathLength",
            u"patterncontentunits":u"patternContentUnits",
            u"patterntransform":u"patternTransform",
            u"patternunits":u"patternUnits",
            u"pointsatx":u"pointsAtX",
            u"pointsaty":u"pointsAtY",
            u"pointsatz":u"pointsAtZ",
            u"preservealpha":u"preserveAlpha",
            u"preserveaspectratio":u"preserveAspectRatio",
            u"primitiveunits":u"primitiveUnits",
            u"refx":u"refX",
            u"refy":u"refY",
            u"repeatcount":u"repeatCount",
            u"repeatdur":u"repeatDur",
            u"requiredextensions":u"requiredExtensions",
            u"requiredfeatures":u"requiredFeatures",
            u"specularconstant":u"specularConstant",
            u"specularexponent":u"specularExponent",
            u"spreadmethod":u"spreadMethod",
            u"startoffset":u"startOffset",
            u"stddeviation":u"stdDeviation",
            u"stitchtiles":u"stitchTiles",
            u"surfacescale":u"surfaceScale",
            u"systemlanguage":u"systemLanguage",
            u"tablevalues":u"tableValues",
            u"targetx":u"targetX",
            u"targety":u"targetY",
            u"textlength":u"textLength",
            u"viewbox":u"viewBox",
            u"viewtarget":u"viewTarget",
            u"xchannelselector":u"xChannelSelector",
            u"ychannelselector":u"yChannelSelector",
            u"zoomandpan":u"zoomAndPan"
            }
        for originalName in list(token[u"data"].keys()):
            if originalName in replacements:
                svgName = replacements[originalName]
                token[u"data"][svgName] = token[u"data"][originalName]
                del token[u"data"][originalName]
    adjustSVGAttributes.func_annotations = {}

    def adjustForeignAttributes(self, token):
        replacements = {
            u"xlink:actuate":(u"xlink", u"actuate", namespaces[u"xlink"]),
            u"xlink:arcrole":(u"xlink", u"arcrole", namespaces[u"xlink"]),
            u"xlink:href":(u"xlink", u"href", namespaces[u"xlink"]),
            u"xlink:role":(u"xlink", u"role", namespaces[u"xlink"]),
            u"xlink:show":(u"xlink", u"show", namespaces[u"xlink"]),
            u"xlink:title":(u"xlink", u"title", namespaces[u"xlink"]),
            u"xlink:type":(u"xlink", u"type", namespaces[u"xlink"]),
            u"xml:base":(u"xml", u"base", namespaces[u"xml"]),
            u"xml:lang":(u"xml", u"lang", namespaces[u"xml"]),
            u"xml:space":(u"xml", u"space", namespaces[u"xml"]),
            u"xmlns":(None, u"xmlns", namespaces[u"xmlns"]),
            u"xmlns:xlink":(u"xmlns", u"xlink", namespaces[u"xmlns"])
            }

        for originalName in token[u"data"].keys():
            if originalName in replacements:
                foreignName = replacements[originalName]
                token[u"data"][foreignName] = token[u"data"][originalName]
                del token[u"data"][originalName]
    adjustForeignAttributes.func_annotations = {}

    def reparseTokenNormal(self, token):
        self.parser.phase()
    reparseTokenNormal.func_annotations = {}

    def resetInsertionMode(self):
        # The name of this method is mostly historical. (It's also used in the
        # specification.)
        last = False
        newModes = {
            u"select":u"inSelect",
            u"td":u"inCell",
            u"th":u"inCell",
            u"tr":u"inRow",
            u"tbody":u"inTableBody",
            u"thead":u"inTableBody",
            u"tfoot":u"inTableBody",
            u"caption":u"inCaption",
            u"colgroup":u"inColumnGroup",
            u"table":u"inTable",
            u"head":u"inBody",
            u"body":u"inBody",
            u"frameset":u"inFrameset",
            u"html":u"beforeHead"
        }
        for node in self.tree.openElements[::-1]:
            nodeName = node.name
            new_phase = None
            if node == self.tree.openElements[0]:
                assert self.innerHTML
                last = True
                nodeName = self.innerHTML
            # Check for conditions that should only happen in the innerHTML
            # case
            if nodeName in (u"select", u"colgroup", u"head", u"html"):
                assert self.innerHTML

            if not last and node.namespace != self.tree.defaultNamespace:
                continue

            if nodeName in newModes:
                new_phase = self.phases[newModes[nodeName]]
                break
            elif last:
                new_phase = self.phases[u"inBody"]
                break

        self.phase = new_phase
    resetInsertionMode.func_annotations = {}

    def parseRCDataRawtext(self, token, contentType):
        u"""Generic RCDATA/RAWTEXT Parsing algorithm
        contentType - RCDATA or RAWTEXT
        """
        assert contentType in (u"RAWTEXT", u"RCDATA")
        
        element = self.tree.insertElement(token)
        
        if contentType == u"RAWTEXT":
            self.tokenizer.state = self.tokenizer.rawtextState
        else:
            self.tokenizer.state = self.tokenizer.rcdataState

        self.originalPhase = self.phase

        self.phase = self.phases[u"text"]
    parseRCDataRawtext.func_annotations = {}

def getPhases(debug):
    def log(function):
        u"""Logger that records which phase processes each token"""
        type_names = dict((value, key) for key, value in 
                          constants.tokenTypes.items())
        def wrapped(self, *args, **kwargs):
            if function.__name__.startswith(u"process") and len(args) > 0:
                token = args[0]
                try:
                    info = {u"type":type_names[token[u'type']]}
                except:
                    raise
                if token[u'type'] in constants.tagTokenTypes:
                    info[u"name"] = token[u'name']

                self.parser.log.append((self.parser.tokenizer.state.__name__,
                                        self.parser.phase.__class__.__name__, 
                                        self.__class__.__name__, 
                                        function.__name__, 
                                        info))
                return function(self, *args, **kwargs)
            else:
                return function(self, *args, **kwargs)
        wrapped.func_annotations = {}
        return wrapped
    log.func_annotations = {}

    def getMetaclass(use_metaclass, metaclass_func):
        if use_metaclass:
            return method_decorator_metaclass(metaclass_func)
        else:
            return type
    getMetaclass.func_annotations = {}

    class Phase(object):
        __metaclass__ = getMetaclass(debug, log)
        u"""Base class for helper object that implements each phase of processing
        """

        def __init__(self, parser, tree):
            self.parser = parser
            self.tree = tree
        __init__.func_annotations = {}

        def processEOF(self):
            raise NotImplementedError
        processEOF.func_annotations = {}

        def processComment(self, token):
            # For most phases the following is correct. Where it's not it will be
            # overridden.
            self.tree.insertComment(token, self.tree.openElements[-1])
        processComment.func_annotations = {}

        def processDoctype(self, token):
            self.parser.parseError(u"unexpected-doctype")
        processDoctype.func_annotations = {}

        def processCharacters(self, token):
            self.tree.insertText(token[u"data"])
        processCharacters.func_annotations = {}

        def processSpaceCharacters(self, token):
            self.tree.insertText(token[u"data"])
        processSpaceCharacters.func_annotations = {}

        def processStartTag(self, token):
            return self.startTagHandler[token[u"name"]](token)
        processStartTag.func_annotations = {}

        def startTagHtml(self, token):
            if self.parser.firstStartTag == False and token[u"name"] == u"html":
               self.parser.parseError(u"non-html-root")
            # XXX Need a check here to see if the first start tag token emitted is
            # this token... If it's not, invoke self.parser.parseError().
            for attr, value in token[u"data"].items():
                if attr not in self.tree.openElements[0].attributes:
                    self.tree.openElements[0].attributes[attr] = value
            self.parser.firstStartTag = False
        startTagHtml.func_annotations = {}

        def processEndTag(self, token):
            return self.endTagHandler[token[u"name"]](token)
        processEndTag.func_annotations = {}

    class InitialPhase(Phase):
        def processSpaceCharacters(self, token):
            pass
        processSpaceCharacters.func_annotations = {}

        def processComment(self, token):
            self.tree.insertComment(token, self.tree.document)
        processComment.func_annotations = {}

        def processDoctype(self, token):
            name = token[u"name"]
            publicId = token[u"publicId"]
            systemId = token[u"systemId"]
            correct = token[u"correct"]

            if (name != u"html" or publicId != None or
                systemId != None and systemId != u"about:legacy-compat"):
                self.parser.parseError(u"unknown-doctype")

            if publicId is None:
                publicId = u""

            self.tree.insertDoctype(token)

            if publicId != u"":
                publicId = publicId.translate(asciiUpper2Lower)

            if (not correct or token[u"name"] != u"html"
                or startswithany(publicId,
                (u"+//silmaril//dtd html pro v0r11 19970101//",
                 u"-//advasoft ltd//dtd html 3.0 aswedit + extensions//",
                 u"-//as//dtd html 3.0 aswedit + extensions//",
                 u"-//ietf//dtd html 2.0 level 1//",
                 u"-//ietf//dtd html 2.0 level 2//",
                 u"-//ietf//dtd html 2.0 strict level 1//",
                 u"-//ietf//dtd html 2.0 strict level 2//",
                 u"-//ietf//dtd html 2.0 strict//",
                 u"-//ietf//dtd html 2.0//",
                 u"-//ietf//dtd html 2.1e//",
                 u"-//ietf//dtd html 3.0//",
                 u"-//ietf//dtd html 3.2 final//",
                 u"-//ietf//dtd html 3.2//",
                 u"-//ietf//dtd html 3//",
                 u"-//ietf//dtd html level 0//",
                 u"-//ietf//dtd html level 1//",
                 u"-//ietf//dtd html level 2//",
                 u"-//ietf//dtd html level 3//",
                 u"-//ietf//dtd html strict level 0//",
                 u"-//ietf//dtd html strict level 1//",
                 u"-//ietf//dtd html strict level 2//",
                 u"-//ietf//dtd html strict level 3//",
                 u"-//ietf//dtd html strict//",
                 u"-//ietf//dtd html//",
                 u"-//metrius//dtd metrius presentational//",
                 u"-//microsoft//dtd internet explorer 2.0 html strict//",
                 u"-//microsoft//dtd internet explorer 2.0 html//",
                 u"-//microsoft//dtd internet explorer 2.0 tables//",
                 u"-//microsoft//dtd internet explorer 3.0 html strict//",
                 u"-//microsoft//dtd internet explorer 3.0 html//",
                 u"-//microsoft//dtd internet explorer 3.0 tables//",
                 u"-//netscape comm. corp.//dtd html//",
                 u"-//netscape comm. corp.//dtd strict html//",
                 u"-//o'reilly and associates//dtd html 2.0//",
                 u"-//o'reilly and associates//dtd html extended 1.0//",
                 u"-//o'reilly and associates//dtd html extended relaxed 1.0//",
                 u"-//softquad software//dtd hotmetal pro 6.0::19990601::extensions to html 4.0//",
                 u"-//softquad//dtd hotmetal pro 4.0::19971010::extensions to html 4.0//",
                 u"-//spyglass//dtd html 2.0 extended//",
                 u"-//sq//dtd html 2.0 hotmetal + extensions//",
                 u"-//sun microsystems corp.//dtd hotjava html//",
                 u"-//sun microsystems corp.//dtd hotjava strict html//",
                 u"-//w3c//dtd html 3 1995-03-24//",
                 u"-//w3c//dtd html 3.2 draft//",
                 u"-//w3c//dtd html 3.2 final//",
                 u"-//w3c//dtd html 3.2//",
                 u"-//w3c//dtd html 3.2s draft//",
                 u"-//w3c//dtd html 4.0 frameset//",
                 u"-//w3c//dtd html 4.0 transitional//",
                 u"-//w3c//dtd html experimental 19960712//",
                 u"-//w3c//dtd html experimental 970421//",
                 u"-//w3c//dtd w3 html//",
                 u"-//w3o//dtd w3 html 3.0//",
                 u"-//webtechs//dtd mozilla html 2.0//",
                 u"-//webtechs//dtd mozilla html//"))
                or publicId in
                    (u"-//w3o//dtd w3 html strict 3.0//en//",
                     u"-/w3c/dtd html 4.0 transitional/en",
                     u"html")
                or startswithany(publicId,
                    (u"-//w3c//dtd html 4.01 frameset//",
                     u"-//w3c//dtd html 4.01 transitional//")) and 
                    systemId == None
                or systemId and systemId.lower() == u"http://www.ibm.com/data/dtd/v11/ibmxhtml1-transitional.dtd"):
                self.parser.compatMode = u"quirks"
            elif (startswithany(publicId,
                    (u"-//w3c//dtd xhtml 1.0 frameset//",
                     u"-//w3c//dtd xhtml 1.0 transitional//"))
                  or startswithany(publicId,
                      (u"-//w3c//dtd html 4.01 frameset//",
                       u"-//w3c//dtd html 4.01 transitional//")) and 
                      systemId != None):
                self.parser.compatMode = u"limited quirks"

            self.parser.phase = self.parser.phases[u"beforeHtml"]
        processDoctype.func_annotations = {}

        def anythingElse(self):
            self.parser.compatMode = u"quirks"
            self.parser.phase = self.parser.phases[u"beforeHtml"]
        anythingElse.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"expected-doctype-but-got-chars")
            self.anythingElse()
            return token
        processCharacters.func_annotations = {}

        def processStartTag(self, token):
            self.parser.parseError(u"expected-doctype-but-got-start-tag",
              {u"name": token[u"name"]})
            self.anythingElse()
            return token
        processStartTag.func_annotations = {}

        def processEndTag(self, token):
            self.parser.parseError(u"expected-doctype-but-got-end-tag",
              {u"name": token[u"name"]})
            self.anythingElse()
            return token
        processEndTag.func_annotations = {}

        def processEOF(self):
            self.parser.parseError(u"expected-doctype-but-got-eof")
            self.anythingElse()
            return True
        processEOF.func_annotations = {}


    class BeforeHtmlPhase(Phase):
        # helper methods
        def insertHtmlElement(self):
            self.tree.insertRoot(impliedTagToken(u"html", u"StartTag"))
            self.parser.phase = self.parser.phases[u"beforeHead"]
        insertHtmlElement.func_annotations = {}

        # other
        def processEOF(self):
            self.insertHtmlElement()
            return True
        processEOF.func_annotations = {}

        def processComment(self, token):
            self.tree.insertComment(token, self.tree.document)
        processComment.func_annotations = {}

        def processSpaceCharacters(self, token):
            pass
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            self.insertHtmlElement()
            return token
        processCharacters.func_annotations = {}

        def processStartTag(self, token):
            if token[u"name"] == u"html":
                self.parser.firstStartTag = True
            self.insertHtmlElement()
            return token
        processStartTag.func_annotations = {}

        def processEndTag(self, token):
            if token[u"name"] not in (u"head", u"body", u"html", u"br"):
                self.parser.parseError(u"unexpected-end-tag-before-html",
                  {u"name": token[u"name"]})
            else:
                self.insertHtmlElement()
                return token
        processEndTag.func_annotations = {}


    class BeforeHeadPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"head", self.startTagHead)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                ((u"head", u"body", u"html", u"br"), self.endTagImplyHead)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            self.startTagHead(impliedTagToken(u"head", u"StartTag"))
            return True
        processEOF.func_annotations = {}

        def processSpaceCharacters(self, token):
            pass
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            self.startTagHead(impliedTagToken(u"head", u"StartTag"))
            return token
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagHead(self, token):
            self.tree.insertElement(token)
            self.tree.headPointer = self.tree.openElements[-1]
            self.parser.phase = self.parser.phases[u"inHead"]
        startTagHead.func_annotations = {}

        def startTagOther(self, token):
            self.startTagHead(impliedTagToken(u"head", u"StartTag"))
            return token
        startTagOther.func_annotations = {}

        def endTagImplyHead(self, token):
            self.startTagHead(impliedTagToken(u"head", u"StartTag"))
            return token
        endTagImplyHead.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"end-tag-after-implied-root",
              {u"name": token[u"name"]})
        endTagOther.func_annotations = {}

    class InHeadPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler =  utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"title", self.startTagTitle),
                ((u"noscript", u"noframes", u"style"), self.startTagNoScriptNoFramesStyle),
                (u"script", self.startTagScript),
                ((u"base", u"basefont", u"bgsound", u"command", u"link"), 
                 self.startTagBaseLinkCommand),
                (u"meta", self.startTagMeta),
                (u"head", self.startTagHead)
            ])
            self.startTagHandler.default = self.startTagOther

            self. endTagHandler = utils.MethodDispatcher([
                (u"head", self.endTagHead),
                ((u"br", u"html", u"body"), self.endTagHtmlBodyBr)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # the real thing
        def processEOF (self):
            self.anythingElse()
            return True
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            self.anythingElse()
            return token
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagHead(self, token):
            self.parser.parseError(u"two-heads-are-not-better-than-one")
        startTagHead.func_annotations = {}

        def startTagBaseLinkCommand(self, token):
            self.tree.insertElement(token)
            self.tree.openElements.pop()
            token[u"selfClosingAcknowledged"] = True
        startTagBaseLinkCommand.func_annotations = {}

        def startTagMeta(self, token):
            self.tree.insertElement(token)
            self.tree.openElements.pop()
            token[u"selfClosingAcknowledged"] = True

            attributes = token[u"data"]
            if self.parser.tokenizer.stream.charEncoding[1] == u"tentative":
                if u"charset" in attributes:
                    self.parser.tokenizer.stream.changeEncoding(attributes[u"charset"])
                elif (u"content" in attributes and
                      u"http-equiv" in attributes and
                      attributes[u"http-equiv"].lower() == u"content-type"):
                    # Encoding it as UTF-8 here is a hack, as really we should pass
                    # the abstract Unicode string, and just use the
                    # ContentAttrParser on that, but using UTF-8 allows all chars
                    # to be encoded and as a ASCII-superset works.
                    data = inputstream.EncodingBytes(attributes[u"content"].encode(u"utf-8"))
                    parser = inputstream.ContentAttrParser(data)
                    codec = parser.parse()
                    self.parser.tokenizer.stream.changeEncoding(codec)
        startTagMeta.func_annotations = {}

        def startTagTitle(self, token):
            self.parser.parseRCDataRawtext(token, u"RCDATA")
        startTagTitle.func_annotations = {}

        def startTagNoScriptNoFramesStyle(self, token):
            #Need to decide whether to implement the scripting-disabled case
            self.parser.parseRCDataRawtext(token, u"RAWTEXT")
        startTagNoScriptNoFramesStyle.func_annotations = {}

        def startTagScript(self, token):
            self.tree.insertElement(token)
            self.parser.tokenizer.state = self.parser.tokenizer.scriptDataState
            self.parser.originalPhase = self.parser.phase
            self.parser.phase = self.parser.phases[u"text"]
        startTagScript.func_annotations = {}

        def startTagOther(self, token):
            self.anythingElse()
            return token
        startTagOther.func_annotations = {}

        def endTagHead(self, token):
            node = self.parser.tree.openElements.pop()
            assert node.name == u"head", u"Expected head got %s"%node.name
            self.parser.phase = self.parser.phases[u"afterHead"]
        endTagHead.func_annotations = {}

        def endTagHtmlBodyBr(self, token):
            self.anythingElse()
            return token
        endTagHtmlBodyBr.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
        endTagOther.func_annotations = {}

        def anythingElse(self):
            self.endTagHead(impliedTagToken(u"head"))
        anythingElse.func_annotations = {}


    # XXX If we implement a parser for which scripting is disabled we need to
    # implement this phase.
    #
    # class InHeadNoScriptPhase(Phase):

    class AfterHeadPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"body", self.startTagBody),
                (u"frameset", self.startTagFrameset),
                ((u"base", u"basefont", u"bgsound", u"link", u"meta", u"noframes", u"script", 
                  u"style", u"title"),
                  self.startTagFromHead),
                (u"head", self.startTagHead)
            ])
            self.startTagHandler.default = self.startTagOther
            self.endTagHandler = utils.MethodDispatcher([((u"body", u"html", u"br"), 
                                                          self.endTagHtmlBodyBr)])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            self.anythingElse()
            return True
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            self.anythingElse()
            return token
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagBody(self, token):
            self.parser.framesetOK = False
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inBody"]
        startTagBody.func_annotations = {}

        def startTagFrameset(self, token):
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inFrameset"]
        startTagFrameset.func_annotations = {}

        def startTagFromHead(self, token):
            self.parser.parseError(u"unexpected-start-tag-out-of-my-head",
              {u"name": token[u"name"]})
            self.tree.openElements.append(self.tree.headPointer)
            self.parser.phases[u"inHead"].processStartTag(token)
            for node in self.tree.openElements[::-1]:
                if node.name == u"head":
                    self.tree.openElements.remove(node)
                    break
        startTagFromHead.func_annotations = {}

        def startTagHead(self, token):
            self.parser.parseError(u"unexpected-start-tag", {u"name":token[u"name"]})
        startTagHead.func_annotations = {}

        def startTagOther(self, token):
            self.anythingElse()
            return token
        startTagOther.func_annotations = {}

        def endTagHtmlBodyBr(self, token):
            self.anythingElse()
            return token
        endTagHtmlBodyBr.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag", {u"name":token[u"name"]})
        endTagOther.func_annotations = {}

        def anythingElse(self):
            self.tree.insertElement(impliedTagToken(u"body", u"StartTag"))
            self.parser.phase = self.parser.phases[u"inBody"]
            self.parser.framesetOK = True
        anythingElse.func_annotations = {}


    class InBodyPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#parsing-main-inbody
        # the really-really-really-very crazy mode
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            #Keep a ref to this for special handling of whitespace in <pre>
            self.processSpaceCharactersNonPre = self.processSpaceCharacters

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                ((u"base", u"basefont", u"bgsound", u"command", u"link", u"meta", 
                  u"noframes", u"script", u"style", u"title"), 
                 self.startTagProcessInHead),
                (u"body", self.startTagBody),
                (u"frameset", self.startTagFrameset),
                ((u"address", u"article", u"aside", u"blockquote", u"center", u"details",
                  u"details", u"dir", u"div", u"dl", u"fieldset", u"figcaption", u"figure",
                  u"footer", u"header", u"hgroup", u"menu", u"nav", u"ol", u"p",
                  u"section", u"summary", u"ul"),
                  self.startTagCloseP),
                (headingElements, self.startTagHeading),
                ((u"pre", u"listing"), self.startTagPreListing),
                (u"form", self.startTagForm),
                ((u"li", u"dd", u"dt"), self.startTagListItem),
                (u"plaintext",self.startTagPlaintext),
                (u"a", self.startTagA),
                ((u"b", u"big", u"code", u"em", u"font", u"i", u"s", u"small", u"strike", 
                  u"strong", u"tt", u"u"),self.startTagFormatting),
                (u"nobr", self.startTagNobr),
                (u"button", self.startTagButton),
                ((u"applet", u"marquee", u"object"), self.startTagAppletMarqueeObject),
                (u"xmp", self.startTagXmp),
                (u"table", self.startTagTable),
                ((u"area", u"br", u"embed", u"img", u"keygen", u"wbr"),
                 self.startTagVoidFormatting),
                ((u"param", u"source", u"track"), self.startTagParamSource),
                (u"input", self.startTagInput),
                (u"hr", self.startTagHr),
                (u"image", self.startTagImage),
                (u"isindex", self.startTagIsIndex),
                (u"textarea", self.startTagTextarea),
                (u"iframe", self.startTagIFrame),
                ((u"noembed", u"noframes", u"noscript"), self.startTagRawtext),
                (u"select", self.startTagSelect),
                ((u"rp", u"rt"), self.startTagRpRt),
                ((u"option", u"optgroup"), self.startTagOpt),
                ((u"math"), self.startTagMath),
                ((u"svg"), self.startTagSvg),
                ((u"caption", u"col", u"colgroup", u"frame", u"head",
                  u"tbody", u"td", u"tfoot", u"th", u"thead",
                  u"tr"), self.startTagMisplaced)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"body",self.endTagBody),
                (u"html",self.endTagHtml),
                ((u"address", u"article", u"aside", u"blockquote", u"center",
                  u"details", u"dir", u"div", u"dl", u"fieldset", u"figcaption", u"figure",
                  u"footer", u"header", u"hgroup", u"listing", u"menu", u"nav", u"ol", u"pre", 
                  u"section", u"summary", u"ul"), self.endTagBlock),
                (u"form", self.endTagForm),
                (u"p",self.endTagP),
                ((u"dd", u"dt", u"li"), self.endTagListItem),
                (headingElements, self.endTagHeading),
                ((u"a", u"b", u"big", u"code", u"em", u"font", u"i", u"nobr", u"s", u"small",
                  u"strike", u"strong", u"tt", u"u"), self.endTagFormatting),
                ((u"applet",  u"marquee", u"object"), self.endTagAppletMarqueeObject),
                (u"br", self.endTagBr),
                ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def isMatchingFormattingElement(self, node1, node2):
            if node1.name != node2.name or node1.namespace != node2.namespace:
                return False
            elif len(node1.attributes) != len(node2.attributes):
                return False
            else:
                attributes1 = sorted(node1.attributes.items())
                attributes2 = sorted(node2.attributes.items())
                for attr1, attr2 in izip(attributes1, attributes2):
                    if attr1 != attr2:
                        return False
            return True
        isMatchingFormattingElement.func_annotations = {}

        # helper
        def addFormattingElement(self, token):
            self.tree.insertElement(token)
            element = self.tree.openElements[-1]
            
            matchingElements = []
            for node in self.tree.activeFormattingElements[::-1]:
                if node is Marker:
                    break
                elif self.isMatchingFormattingElement(node, element):
                    matchingElements.append(node)
                    
            assert len(matchingElements) <= 3
            if len(matchingElements) == 3:
                self.tree.activeFormattingElements.remove(matchingElements[-1])
            self.tree.activeFormattingElements.append(element)
        addFormattingElement.func_annotations = {}

        # the real deal
        def processEOF(self):
            allowed_elements = frozenset((u"dd", u"dt", u"li", u"p", u"tbody", u"td",
                                          u"tfoot", u"th", u"thead", u"tr", u"body",
                                          u"html"))
            for node in self.tree.openElements[::-1]:
                if node.name not in allowed_elements:
                    self.parser.parseError(u"expected-closing-tag-but-got-eof")
                    break
        processEOF.func_annotations = {}
            #Stop parsing

        def processSpaceCharactersDropNewline(self, token):
            # Sometimes (start of <pre>, <listing>, and <textarea> blocks) we
            # want to drop leading newlines
            data = token[u"data"]
            self.processSpaceCharacters = self.processSpaceCharactersNonPre
            if (data.startswith(u"\n") and
                self.tree.openElements[-1].name in (u"pre", u"listing", u"textarea")
                and not self.tree.openElements[-1].hasContent()):
                data = data[1:]
            if data:
                self.tree.reconstructActiveFormattingElements()
                self.tree.insertText(data)
        processSpaceCharactersDropNewline.func_annotations = {}

        def processCharacters(self, token):
            if token[u"data"] == u"\u0000":
                #The tokenizer should always emit null on its own
                return
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertText(token[u"data"])
            #This must be bad for performance
            if (self.parser.framesetOK and
                any([char not in spaceCharacters
                     for char in token[u"data"]])):
                self.parser.framesetOK = False
        processCharacters.func_annotations = {}

        def processSpaceCharacters(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertText(token[u"data"])
        processSpaceCharacters.func_annotations = {}

        def startTagProcessInHead(self, token):
            return self.parser.phases[u"inHead"].processStartTag(token)
        startTagProcessInHead.func_annotations = {}

        def startTagBody(self, token):
            self.parser.parseError(u"unexpected-start-tag", {u"name": u"body"})
            if (len(self.tree.openElements) == 1
                or self.tree.openElements[1].name != u"body"):
                assert self.parser.innerHTML
            else:
                self.parser.framesetOK = False
                for attr, value in token[u"data"].items():
                    if attr not in self.tree.openElements[1].attributes:
                        self.tree.openElements[1].attributes[attr] = value
        startTagBody.func_annotations = {}

        def startTagFrameset(self, token):
            self.parser.parseError(u"unexpected-start-tag", {u"name": u"frameset"})
            if (len(self.tree.openElements) == 1 or self.tree.openElements[1].name != u"body"):
                assert self.parser.innerHTML
            elif not self.parser.framesetOK:
                pass
            else:
                if self.tree.openElements[1].parent:
                    self.tree.openElements[1].parent.removeChild(self.tree.openElements[1])
                while self.tree.openElements[-1].name != u"html":
                    self.tree.openElements.pop()
                self.tree.insertElement(token)
                self.parser.phase = self.parser.phases[u"inFrameset"]
        startTagFrameset.func_annotations = {}

        def startTagCloseP(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            self.tree.insertElement(token)
        startTagCloseP.func_annotations = {}

        def startTagPreListing(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            self.tree.insertElement(token)
            self.parser.framesetOK = False
            self.processSpaceCharacters = self.processSpaceCharactersDropNewline
        startTagPreListing.func_annotations = {}

        def startTagForm(self, token):
            if self.tree.formPointer:
                self.parser.parseError(u"unexpected-start-tag", {u"name": u"form"})
            else:
                if self.tree.elementInScope(u"p", variant=u"button"):
                    self.endTagP(impliedTagToken(u"p"))
                self.tree.insertElement(token)
                self.tree.formPointer = self.tree.openElements[-1]
        startTagForm.func_annotations = {}

        def startTagListItem(self, token):
            self.parser.framesetOK = False

            stopNamesMap = {u"li":[u"li"],
                            u"dt":[u"dt", u"dd"],
                            u"dd":[u"dt", u"dd"]}
            stopNames = stopNamesMap[token[u"name"]]
            for node in reversed(self.tree.openElements):
                if node.name in stopNames:
                    self.parser.phase.processEndTag(
                        impliedTagToken(node.name, u"EndTag"))
                    break
                if (node.nameTuple in specialElements and
                    node.name not in (u"address", u"div", u"p")):
                    break

            if self.tree.elementInScope(u"p", variant=u"button"):
                self.parser.phase.processEndTag(
                    impliedTagToken(u"p", u"EndTag"))

            self.tree.insertElement(token)
        startTagListItem.func_annotations = {}

        def startTagPlaintext(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            self.tree.insertElement(token)
            self.parser.tokenizer.state = self.parser.tokenizer.plaintextState
        startTagPlaintext.func_annotations = {}

        def startTagHeading(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            if self.tree.openElements[-1].name in headingElements:
                self.parser.parseError(u"unexpected-start-tag", {u"name": token[u"name"]})
                self.tree.openElements.pop()
            self.tree.insertElement(token)
        startTagHeading.func_annotations = {}

        def startTagA(self, token):
            afeAElement = self.tree.elementInActiveFormattingElements(u"a")
            if afeAElement:
                self.parser.parseError(u"unexpected-start-tag-implies-end-tag",
                  {u"startName": u"a", u"endName": u"a"})
                self.endTagFormatting(impliedTagToken(u"a"))
                if afeAElement in self.tree.openElements:
                    self.tree.openElements.remove(afeAElement)
                if afeAElement in self.tree.activeFormattingElements:
                    self.tree.activeFormattingElements.remove(afeAElement)
            self.tree.reconstructActiveFormattingElements()
            self.addFormattingElement(token)
        startTagA.func_annotations = {}

        def startTagFormatting(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.addFormattingElement(token)
        startTagFormatting.func_annotations = {}

        def startTagNobr(self, token):
            self.tree.reconstructActiveFormattingElements()
            if self.tree.elementInScope(u"nobr"):
                self.parser.parseError(u"unexpected-start-tag-implies-end-tag",
                  {u"startName": u"nobr", u"endName": u"nobr"})
                self.processEndTag(impliedTagToken(u"nobr"))
                # XXX Need tests that trigger the following
                self.tree.reconstructActiveFormattingElements()
            self.addFormattingElement(token)
        startTagNobr.func_annotations = {}

        def startTagButton(self, token):
            if self.tree.elementInScope(u"button"):
                self.parser.parseError(u"unexpected-start-tag-implies-end-tag",
                  {u"startName": u"button", u"endName": u"button"})
                self.processEndTag(impliedTagToken(u"button"))
                return token
            else:
                self.tree.reconstructActiveFormattingElements()
                self.tree.insertElement(token)
                self.parser.framesetOK = False
        startTagButton.func_annotations = {}

        def startTagAppletMarqueeObject(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(token)
            self.tree.activeFormattingElements.append(Marker)
            self.parser.framesetOK = False
        startTagAppletMarqueeObject.func_annotations = {}

        def startTagXmp(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            self.tree.reconstructActiveFormattingElements()
            self.parser.framesetOK = False
            self.parser.parseRCDataRawtext(token, u"RAWTEXT")
        startTagXmp.func_annotations = {}

        def startTagTable(self, token):
            if self.parser.compatMode != u"quirks":
                if self.tree.elementInScope(u"p", variant=u"button"):
                    self.processEndTag(impliedTagToken(u"p"))
            self.tree.insertElement(token)
            self.parser.framesetOK = False
            self.parser.phase = self.parser.phases[u"inTable"]
        startTagTable.func_annotations = {}

        def startTagVoidFormatting(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(token)
            self.tree.openElements.pop()
            token[u"selfClosingAcknowledged"] = True
            self.parser.framesetOK = False
        startTagVoidFormatting.func_annotations = {}

        def startTagInput(self, token):
            framesetOK = self.parser.framesetOK
            self.startTagVoidFormatting(token)
            if (u"type" in token[u"data"] and
                token[u"data"][u"type"].translate(asciiUpper2Lower) == u"hidden"):
                #input type=hidden doesn't change framesetOK
                self.parser.framesetOK = framesetOK
        startTagInput.func_annotations = {}

        def startTagParamSource(self, token):
            self.tree.insertElement(token)
            self.tree.openElements.pop()
            token[u"selfClosingAcknowledged"] = True
        startTagParamSource.func_annotations = {}

        def startTagHr(self, token):
            if self.tree.elementInScope(u"p", variant=u"button"):
                self.endTagP(impliedTagToken(u"p"))
            self.tree.insertElement(token)
            self.tree.openElements.pop()
            token[u"selfClosingAcknowledged"] = True
            self.parser.framesetOK = False
        startTagHr.func_annotations = {}

        def startTagImage(self, token):
            # No really...
            self.parser.parseError(u"unexpected-start-tag-treated-as",
              {u"originalName": u"image", u"newName": u"img"})
            self.processStartTag(impliedTagToken(u"img", u"StartTag",
                                                 attributes=token[u"data"],
                                                 selfClosing=token[u"selfClosing"]))
        startTagImage.func_annotations = {}

        def startTagIsIndex(self, token):
            self.parser.parseError(u"deprecated-tag", {u"name": u"isindex"})
            if self.tree.formPointer:
                return
            form_attrs = {}
            if u"action" in token[u"data"]:
                form_attrs[u"action"] = token[u"data"][u"action"]
            self.processStartTag(impliedTagToken(u"form", u"StartTag",
                                                 attributes=form_attrs))
            self.processStartTag(impliedTagToken(u"hr", u"StartTag"))
            self.processStartTag(impliedTagToken(u"label", u"StartTag"))
            # XXX Localization ...
            if u"prompt" in token[u"data"]:
                prompt = token[u"data"][u"prompt"]
            else:
                prompt = u"This is a searchable index. Enter search keywords: "
            self.processCharacters(
                {u"type":tokenTypes[u"Characters"], u"data":prompt})
            attributes = token[u"data"].copy()
            if u"action" in attributes:
                del attributes[u"action"]
            if u"prompt" in attributes:
                del attributes[u"prompt"]
            attributes[u"name"] = u"isindex"
            self.processStartTag(impliedTagToken(u"input", u"StartTag", 
                                                 attributes = attributes,
                                                 selfClosing = 
                                                 token[u"selfClosing"]))
            self.processEndTag(impliedTagToken(u"label"))
            self.processStartTag(impliedTagToken(u"hr", u"StartTag"))
            self.processEndTag(impliedTagToken(u"form"))
        startTagIsIndex.func_annotations = {}

        def startTagTextarea(self, token):
            self.tree.insertElement(token)
            self.parser.tokenizer.state = self.parser.tokenizer.rcdataState
            self.processSpaceCharacters = self.processSpaceCharactersDropNewline
            self.parser.framesetOK = False
        startTagTextarea.func_annotations = {}

        def startTagIFrame(self, token):
            self.parser.framesetOK = False
            self.startTagRawtext(token)
        startTagIFrame.func_annotations = {}

        def startTagRawtext(self, token):
            u"""iframe, noembed noframes, noscript(if scripting enabled)"""
            self.parser.parseRCDataRawtext(token, u"RAWTEXT")
        startTagRawtext.func_annotations = {}

        def startTagOpt(self, token):
            if self.tree.openElements[-1].name == u"option":
                self.parser.phase.processEndTag(impliedTagToken(u"option"))
            self.tree.reconstructActiveFormattingElements()
            self.parser.tree.insertElement(token)
        startTagOpt.func_annotations = {}

        def startTagSelect(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(token)
            self.parser.framesetOK = False
            if self.parser.phase in (self.parser.phases[u"inTable"],
                                     self.parser.phases[u"inCaption"],
                                     self.parser.phases[u"inColumnGroup"],
                                     self.parser.phases[u"inTableBody"], 
                                     self.parser.phases[u"inRow"],
                                     self.parser.phases[u"inCell"]):
                self.parser.phase = self.parser.phases[u"inSelectInTable"]
            else:
                self.parser.phase = self.parser.phases[u"inSelect"]
        startTagSelect.func_annotations = {}

        def startTagRpRt(self, token):
            if self.tree.elementInScope(u"ruby"):
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != u"ruby":
                    self.parser.parseError()
            self.tree.insertElement(token)
        startTagRpRt.func_annotations = {}

        def startTagMath(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.parser.adjustMathMLAttributes(token)
            self.parser.adjustForeignAttributes(token)
            token[u"namespace"] = namespaces[u"mathml"]
            self.tree.insertElement(token)
            #Need to get the parse error right for the case where the token 
            #has a namespace not equal to the xmlns attribute
            if token[u"selfClosing"]:
                self.tree.openElements.pop()
                token[u"selfClosingAcknowledged"] = True
        startTagMath.func_annotations = {}

        def startTagSvg(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.parser.adjustSVGAttributes(token)
            self.parser.adjustForeignAttributes(token)
            token[u"namespace"] = namespaces[u"svg"]
            self.tree.insertElement(token)
            #Need to get the parse error right for the case where the token 
            #has a namespace not equal to the xmlns attribute
            if token[u"selfClosing"]:
                self.tree.openElements.pop()
                token[u"selfClosingAcknowledged"] = True
        startTagSvg.func_annotations = {}

        def startTagMisplaced(self, token):
            u""" Elements that should be children of other elements that have a
            different insertion mode; here they are ignored
            "caption", "col", "colgroup", "frame", "frameset", "head",
            "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
            "tr", "noscript"
            """
            self.parser.parseError(u"unexpected-start-tag-ignored", {u"name": token[u"name"]})
        startTagMisplaced.func_annotations = {}

        def startTagOther(self, token):
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(token)
        startTagOther.func_annotations = {}

        def endTagP(self, token):
            if not self.tree.elementInScope(u"p", variant=u"button"):
                self.startTagCloseP(impliedTagToken(u"p", u"StartTag"))
                self.parser.parseError(u"unexpected-end-tag", {u"name": u"p"})
                self.endTagP(impliedTagToken(u"p", u"EndTag"))
            else:
                self.tree.generateImpliedEndTags(u"p")
                if self.tree.openElements[-1].name != u"p":
                    self.parser.parseError(u"unexpected-end-tag", {u"name": u"p"})
                node = self.tree.openElements.pop()
                while node.name != u"p":
                    node = self.tree.openElements.pop()
        endTagP.func_annotations = {}

        def endTagBody(self, token):
            if not self.tree.elementInScope(u"body"):
                self.parser.parseError()
                return
            elif self.tree.openElements[-1].name != u"body":
                for node in self.tree.openElements[2:]:
                    if node.name not in frozenset((u"dd", u"dt", u"li", u"optgroup",
                                                   u"option", u"p", u"rp", u"rt",
                                                   u"tbody", u"td", u"tfoot",
                                                   u"th", u"thead", u"tr", u"body",
                                                   u"html")):
                        #Not sure this is the correct name for the parse error
                        self.parser.parseError(
                            u"expected-one-end-tag-but-got-another",
                            {u"expectedName": u"body", u"gotName": node.name})
                        break
            self.parser.phase = self.parser.phases[u"afterBody"]
        endTagBody.func_annotations = {}

        def endTagHtml(self, token):
            #We repeat the test for the body end tag token being ignored here
            if self.tree.elementInScope(u"body"):
                self.endTagBody(impliedTagToken(u"body"))
                return token
        endTagHtml.func_annotations = {}

        def endTagBlock(self, token):
            #Put us back in the right whitespace handling mode
            if token[u"name"] == u"pre":
                self.processSpaceCharacters = self.processSpaceCharactersNonPre
            inScope = self.tree.elementInScope(token[u"name"])
            if inScope:
                self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != token[u"name"]:
                 self.parser.parseError(u"end-tag-too-early", {u"name": token[u"name"]})
            if inScope:
                node = self.tree.openElements.pop()
                while node.name != token[u"name"]:
                    node = self.tree.openElements.pop()
        endTagBlock.func_annotations = {}

        def endTagForm(self, token):
            node = self.tree.formPointer
            self.tree.formPointer = None
            if node is None or not self.tree.elementInScope(node):
                self.parser.parseError(u"unexpected-end-tag",
                                       {u"name":u"form"})
            else:
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1] != node:
                    self.parser.parseError(u"end-tag-too-early-ignored",
                                           {u"name": u"form"})
                self.tree.openElements.remove(node)
        endTagForm.func_annotations = {}

        def endTagListItem(self, token):
            if token[u"name"] == u"li":
                variant = u"list"
            else:
                variant = None
            if not self.tree.elementInScope(token[u"name"], variant=variant):
                self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
            else:
                self.tree.generateImpliedEndTags(exclude = token[u"name"])
                if self.tree.openElements[-1].name != token[u"name"]:
                    self.parser.parseError(
                        u"end-tag-too-early",
                        {u"name": token[u"name"]})
                node = self.tree.openElements.pop()
                while node.name != token[u"name"]:
                    node = self.tree.openElements.pop()
        endTagListItem.func_annotations = {}

        def endTagHeading(self, token):
            for item in headingElements:
                if self.tree.elementInScope(item):
                    self.tree.generateImpliedEndTags()
                    break
            if self.tree.openElements[-1].name != token[u"name"]:
                self.parser.parseError(u"end-tag-too-early", {u"name": token[u"name"]})

            for item in headingElements:
                if self.tree.elementInScope(item):
                    item = self.tree.openElements.pop()
                    while item.name not in headingElements:
                        item = self.tree.openElements.pop()
                    break
        endTagHeading.func_annotations = {}

        def endTagFormatting(self, token):
            u"""The much-feared adoption agency algorithm"""
            # http://www.whatwg.org/specs/web-apps/current-work/#adoptionAgency
            # XXX Better parseError messages appreciated.
            name = token[u"name"]

            outerLoopCounter = 0
            while outerLoopCounter < 8:
                outerLoopCounter += 1

                # Step 1 paragraph 1
                formattingElement = self.tree.elementInActiveFormattingElements(
                    token[u"name"])
                if (not formattingElement or 
                    (formattingElement in self.tree.openElements and
                     not self.tree.elementInScope(formattingElement.name))):
                    self.parser.parseError(u"adoption-agency-1.1", {u"name": token[u"name"]})
                    return

                # Step 1 paragraph 2
                elif formattingElement not in self.tree.openElements:
                    self.parser.parseError(u"adoption-agency-1.2", {u"name": token[u"name"]})
                    self.tree.activeFormattingElements.remove(formattingElement)
                    return

                # Step 1 paragraph 3
                if formattingElement != self.tree.openElements[-1]:
                    self.parser.parseError(u"adoption-agency-1.3", {u"name": token[u"name"]})

                # Step 2
                # Start of the adoption agency algorithm proper
                afeIndex = self.tree.openElements.index(formattingElement)
                furthestBlock = None
                for element in self.tree.openElements[afeIndex:]:
                    if element.nameTuple in specialElements:
                        furthestBlock = element
                        break
                # Step 3
                if furthestBlock is None:
                    element = self.tree.openElements.pop()
                    while element != formattingElement:
                        element = self.tree.openElements.pop()
                    self.tree.activeFormattingElements.remove(element)
                    return
                commonAncestor = self.tree.openElements[afeIndex-1]

                # Step 5
                #if furthestBlock.parent:
                #    furthestBlock.parent.removeChild(furthestBlock)

                # Step 5
                # The bookmark is supposed to help us identify where to reinsert
                # nodes in step 12. We have to ensure that we reinsert nodes after
                # the node before the active formatting element. Note the bookmark
                # can move in step 7.4
                bookmark = self.tree.activeFormattingElements.index(formattingElement)

                # Step 6
                lastNode = node = furthestBlock
                innerLoopCounter = 0
                
                index = self.tree.openElements.index(node)
                while innerLoopCounter < 3:
                    innerLoopCounter += 1
                    # Node is element before node in open elements
                    index -= 1
                    node = self.tree.openElements[index]
                    if node not in self.tree.activeFormattingElements:
                        self.tree.openElements.remove(node)
                        continue
                    # Step 6.3
                    if node == formattingElement:
                        break
                    # Step 6.4
                    if lastNode == furthestBlock:
                        bookmark = (self.tree.activeFormattingElements.index(node)
                                    + 1)
                    # Step 6.5
                    #cite = node.parent
                    clone = node.cloneNode()
                    # Replace node with clone
                    self.tree.activeFormattingElements[
                        self.tree.activeFormattingElements.index(node)] = clone
                    self.tree.openElements[
                        self.tree.openElements.index(node)] = clone
                    node = clone

                    # Step 6.6
                    # Remove lastNode from its parents, if any
                    if lastNode.parent:
                        lastNode.parent.removeChild(lastNode)
                    node.appendChild(lastNode)
                    # Step 7.7
                    lastNode = node
                    # End of inner loop 

                # Step 7
                # Foster parent lastNode if commonAncestor is a
                # table, tbody, tfoot, thead, or tr we need to foster parent the 
                # lastNode
                if lastNode.parent:
                    lastNode.parent.removeChild(lastNode)

                if commonAncestor.name in frozenset((u"table", u"tbody", u"tfoot", u"thead", u"tr")):
                    parent, insertBefore = self.tree.getTableMisnestedNodePosition()
                    parent.insertBefore(lastNode, insertBefore)
                else:
                    commonAncestor.appendChild(lastNode)

                # Step 8
                clone = formattingElement.cloneNode()

                # Step 9
                furthestBlock.reparentChildren(clone)

                # Step 10
                furthestBlock.appendChild(clone)

                # Step 11
                self.tree.activeFormattingElements.remove(formattingElement)
                self.tree.activeFormattingElements.insert(bookmark, clone)

                # Step 12
                self.tree.openElements.remove(formattingElement)
                self.tree.openElements.insert(
                  self.tree.openElements.index(furthestBlock) + 1, clone)
        endTagFormatting.func_annotations = {}

        def endTagAppletMarqueeObject(self, token):
            if self.tree.elementInScope(token[u"name"]):
                self.tree.generateImpliedEndTags()
            if self.tree.openElements[-1].name != token[u"name"]:
                self.parser.parseError(u"end-tag-too-early", {u"name": token[u"name"]})

            if self.tree.elementInScope(token[u"name"]):
                element = self.tree.openElements.pop()
                while element.name != token[u"name"]:
                    element = self.tree.openElements.pop()
                self.tree.clearActiveFormattingElements()
        endTagAppletMarqueeObject.func_annotations = {}

        def endTagBr(self, token):
            self.parser.parseError(u"unexpected-end-tag-treated-as",
              {u"originalName": u"br", u"newName": u"br element"})
            self.tree.reconstructActiveFormattingElements()
            self.tree.insertElement(impliedTagToken(u"br", u"StartTag"))
            self.tree.openElements.pop()
        endTagBr.func_annotations = {}

        def endTagOther(self, token):
            for node in self.tree.openElements[::-1]:
                if node.name == token[u"name"]:
                    self.tree.generateImpliedEndTags(exclude=token[u"name"])
                    if self.tree.openElements[-1].name != token[u"name"]:
                        self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
                    while self.tree.openElements.pop() != node:
                        pass
                    break
                else:
                    if node.nameTuple in specialElements:
                        self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
                        break
        endTagOther.func_annotations = {}

    class TextPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.startTagHandler = utils.MethodDispatcher([])
            self.startTagHandler.default = self.startTagOther
            self.endTagHandler = utils.MethodDispatcher([
                    (u"script", self.endTagScript)])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processCharacters(self, token):
            self.tree.insertText(token[u"data"])
        processCharacters.func_annotations = {}

        def processEOF(self):
            self.parser.parseError(u"expected-named-closing-tag-but-got-eof", 
                                   self.tree.openElements[-1].name)
            self.tree.openElements.pop()
            self.parser.phase = self.parser.originalPhase
            return True
        processEOF.func_annotations = {}

        def startTagOther(self, token):
            assert False, u"Tried to process start tag %s in RCDATA/RAWTEXT mode"%token[u'name']
        startTagOther.func_annotations = {}

        def endTagScript(self, token):
            node = self.tree.openElements.pop()
            assert node.name == u"script"
            self.parser.phase = self.parser.originalPhase
        endTagScript.func_annotations = {}
            #The rest of this method is all stuff that only happens if
            #document.write works

        def endTagOther(self, token):
            node = self.tree.openElements.pop()
            self.parser.phase = self.parser.originalPhase
        endTagOther.func_annotations = {}

    class InTablePhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-table
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"caption", self.startTagCaption),
                (u"colgroup", self.startTagColgroup),
                (u"col", self.startTagCol),
                ((u"tbody", u"tfoot", u"thead"), self.startTagRowGroup),
                ((u"td", u"th", u"tr"), self.startTagImplyTbody),
                (u"table", self.startTagTable),
                ((u"style", u"script"), self.startTagStyleScript),
                (u"input", self.startTagInput),
                (u"form", self.startTagForm)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"table", self.endTagTable),
                ((u"body", u"caption", u"col", u"colgroup", u"html", u"tbody", u"td",
                  u"tfoot", u"th", u"thead", u"tr"), self.endTagIgnore)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # helper methods
        def clearStackToTableContext(self):
            # "clear the stack back to a table context"
            while self.tree.openElements[-1].name not in (u"table", u"html"):
                #self.parser.parseError("unexpected-implied-end-tag-in-table",
                #  {"name":  self.tree.openElements[-1].name})
                self.tree.openElements.pop()
        clearStackToTableContext.func_annotations = {}
            # When the current node is <html> it's an innerHTML case

        # processing methods
        def processEOF(self):
            if self.tree.openElements[-1].name != u"html":
                self.parser.parseError(u"eof-in-table")
            else:
                assert self.parser.innerHTML
        processEOF.func_annotations = {}
            #Stop parsing

        def processSpaceCharacters(self, token):
            originalPhase = self.parser.phase
            self.parser.phase = self.parser.phases[u"inTableText"]
            self.parser.phase.originalPhase = originalPhase
            self.parser.phase.processSpaceCharacters(token)
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            originalPhase = self.parser.phase
            self.parser.phase = self.parser.phases[u"inTableText"]
            self.parser.phase.originalPhase = originalPhase
            self.parser.phase.processCharacters(token)
        processCharacters.func_annotations = {}

        def insertText(self, token):
            #If we get here there must be at least one non-whitespace character
            # Do the table magic!
            self.tree.insertFromTable = True
            self.parser.phases[u"inBody"].processCharacters(token)
            self.tree.insertFromTable = False
        insertText.func_annotations = {}

        def startTagCaption(self, token):
            self.clearStackToTableContext()
            self.tree.activeFormattingElements.append(Marker)
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inCaption"]
        startTagCaption.func_annotations = {}

        def startTagColgroup(self, token):
            self.clearStackToTableContext()
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inColumnGroup"]
        startTagColgroup.func_annotations = {}

        def startTagCol(self, token):
            self.startTagColgroup(impliedTagToken(u"colgroup", u"StartTag"))
            return token
        startTagCol.func_annotations = {}

        def startTagRowGroup(self, token):
            self.clearStackToTableContext()
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inTableBody"]
        startTagRowGroup.func_annotations = {}

        def startTagImplyTbody(self, token):
            self.startTagRowGroup(impliedTagToken(u"tbody", u"StartTag"))
            return token
        startTagImplyTbody.func_annotations = {}

        def startTagTable(self, token):
            self.parser.parseError(u"unexpected-start-tag-implies-end-tag",
              {u"startName": u"table", u"endName": u"table"})
            self.parser.phase.processEndTag(impliedTagToken(u"table"))
            if not self.parser.innerHTML:
                return token
        startTagTable.func_annotations = {}

        def startTagStyleScript(self, token):
            return self.parser.phases[u"inHead"].processStartTag(token)
        startTagStyleScript.func_annotations = {}

        def startTagInput(self, token):
            if (u"type" in token[u"data"] and 
                token[u"data"][u"type"].translate(asciiUpper2Lower) == u"hidden"):
                self.parser.parseError(u"unexpected-hidden-input-in-table")
                self.tree.insertElement(token)
                # XXX associate with form
                self.tree.openElements.pop()
            else:
                self.startTagOther(token)
        startTagInput.func_annotations = {}

        def startTagForm(self, token):
            self.parser.parseError(u"unexpected-form-in-table")
            if self.tree.formPointer is None:
                self.tree.insertElement(token)
                self.tree.formPointer = self.tree.openElements[-1]
                self.tree.openElements.pop()
        startTagForm.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"unexpected-start-tag-implies-table-voodoo", {u"name": token[u"name"]})
            # Do the table magic!
            self.tree.insertFromTable = True
            self.parser.phases[u"inBody"].processStartTag(token)
            self.tree.insertFromTable = False
        startTagOther.func_annotations = {}

        def endTagTable(self, token):
            if self.tree.elementInScope(u"table", variant=u"table"):
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != u"table":
                    self.parser.parseError(u"end-tag-too-early-named",
                      {u"gotName": u"table",
                       u"expectedName": self.tree.openElements[-1].name})
                while self.tree.openElements[-1].name != u"table":
                    self.tree.openElements.pop()
                self.tree.openElements.pop()
                self.parser.resetInsertionMode()
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        endTagTable.func_annotations = {}

        def endTagIgnore(self, token):
            self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
        endTagIgnore.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag-implies-table-voodoo", {u"name": token[u"name"]})
            # Do the table magic!
            self.tree.insertFromTable = True
            self.parser.phases[u"inBody"].processEndTag(token)
            self.tree.insertFromTable = False
        endTagOther.func_annotations = {}

    class InTableTextPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.originalPhase = None
            self.characterTokens = []
        __init__.func_annotations = {}

        def flushCharacters(self):
            data = u"".join([item[u"data"] for item in self.characterTokens])
            if any([item not in spaceCharacters for item in data]):
                token = {u"type":tokenTypes[u"Characters"], u"data":data}
                self.parser.phases[u"inTable"].insertText(token)
            elif data:
                self.tree.insertText(data)
            self.characterTokens = []
        flushCharacters.func_annotations = {}

        def processComment(self, token):
            self.flushCharacters()
            self.parser.phase = self.originalPhase
            return token
        processComment.func_annotations = {}

        def processEOF(self):
            self.flushCharacters()
            self.parser.phase = self.originalPhase
            return True
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            if token[u"data"] == u"\u0000":
                return
            self.characterTokens.append(token)
        processCharacters.func_annotations = {}

        def processSpaceCharacters(self, token):
            #pretty sure we should never reach here
            self.characterTokens.append(token)
        processSpaceCharacters.func_annotations = {}
    #        assert False

        def processStartTag(self, token):
            self.flushCharacters()
            self.parser.phase = self.originalPhase
            return token
        processStartTag.func_annotations = {}

        def processEndTag(self, token):
            self.flushCharacters()
            self.parser.phase = self.originalPhase
            return token
        processEndTag.func_annotations = {}


    class InCaptionPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-caption
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                ((u"caption", u"col", u"colgroup", u"tbody", u"td", u"tfoot", u"th",
                  u"thead", u"tr"), self.startTagTableElement)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"caption", self.endTagCaption),
                (u"table", self.endTagTable),
                ((u"body", u"col", u"colgroup", u"html", u"tbody", u"td", u"tfoot", u"th",
                  u"thead", u"tr"), self.endTagIgnore)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def ignoreEndTagCaption(self):
            return not self.tree.elementInScope(u"caption", variant=u"table")
        ignoreEndTagCaption.func_annotations = {}

        def processEOF(self):
            self.parser.phases[u"inBody"].processEOF()
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            return self.parser.phases[u"inBody"].processCharacters(token)
        processCharacters.func_annotations = {}

        def startTagTableElement(self, token):
            self.parser.parseError()
            #XXX Have to duplicate logic here to find out if the tag is ignored
            ignoreEndTag = self.ignoreEndTagCaption()
            self.parser.phase.processEndTag(impliedTagToken(u"caption"))
            if not ignoreEndTag:
                return token
        startTagTableElement.func_annotations = {}

        def startTagOther(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagOther.func_annotations = {}

        def endTagCaption(self, token):
            if not self.ignoreEndTagCaption():
                # AT this code is quite similar to endTagTable in "InTable"
                self.tree.generateImpliedEndTags()
                if self.tree.openElements[-1].name != u"caption":
                    self.parser.parseError(u"expected-one-end-tag-but-got-another",
                      {u"gotName": u"caption",
                       u"expectedName": self.tree.openElements[-1].name})
                while self.tree.openElements[-1].name != u"caption":
                    self.tree.openElements.pop()
                self.tree.openElements.pop()
                self.tree.clearActiveFormattingElements()
                self.parser.phase = self.parser.phases[u"inTable"]
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        endTagCaption.func_annotations = {}

        def endTagTable(self, token):
            self.parser.parseError()
            ignoreEndTag = self.ignoreEndTagCaption()
            self.parser.phase.processEndTag(impliedTagToken(u"caption"))
            if not ignoreEndTag:
                return token
        endTagTable.func_annotations = {}

        def endTagIgnore(self, token):
            self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
        endTagIgnore.func_annotations = {}

        def endTagOther(self, token):
            return self.parser.phases[u"inBody"].processEndTag(token)
        endTagOther.func_annotations = {}


    class InColumnGroupPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-column

        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"col", self.startTagCol)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"colgroup", self.endTagColgroup),
                (u"col", self.endTagCol)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def ignoreEndTagColgroup(self):
            return self.tree.openElements[-1].name == u"html"
        ignoreEndTagColgroup.func_annotations = {}

        def processEOF(self):
            if self.tree.openElements[-1].name == u"html":
                assert self.parser.innerHTML
                return
            else:
                ignoreEndTag = self.ignoreEndTagColgroup()
                self.endTagColgroup(impliedTagToken(u"colgroup"))
                if not ignoreEndTag:
                    return True
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            ignoreEndTag = self.ignoreEndTagColgroup()
            self.endTagColgroup(impliedTagToken(u"colgroup"))
            if not ignoreEndTag:
                return token
        processCharacters.func_annotations = {}

        def startTagCol(self, token):
            self.tree.insertElement(token)
            self.tree.openElements.pop()
        startTagCol.func_annotations = {}

        def startTagOther(self, token):
            ignoreEndTag = self.ignoreEndTagColgroup()
            self.endTagColgroup(impliedTagToken(u"colgroup"))
            if not ignoreEndTag:
                return token
        startTagOther.func_annotations = {}

        def endTagColgroup(self, token):
            if self.ignoreEndTagColgroup():
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
            else:
                self.tree.openElements.pop()
                self.parser.phase = self.parser.phases[u"inTable"]
        endTagColgroup.func_annotations = {}

        def endTagCol(self, token):
            self.parser.parseError(u"no-end-tag", {u"name": u"col"})
        endTagCol.func_annotations = {}

        def endTagOther(self, token):
            ignoreEndTag = self.ignoreEndTagColgroup()
            self.endTagColgroup(impliedTagToken(u"colgroup"))
            if not ignoreEndTag:
                return token
        endTagOther.func_annotations = {}


    class InTableBodyPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-table0
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"tr", self.startTagTr),
                ((u"td", u"th"), self.startTagTableCell),
                ((u"caption", u"col", u"colgroup", u"tbody", u"tfoot", u"thead"),
                 self.startTagTableOther)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                ((u"tbody", u"tfoot", u"thead"), self.endTagTableRowGroup),
                (u"table", self.endTagTable),
                ((u"body", u"caption", u"col", u"colgroup", u"html", u"td", u"th",
                  u"tr"), self.endTagIgnore)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # helper methods
        def clearStackToTableBodyContext(self):
            while self.tree.openElements[-1].name not in (u"tbody", u"tfoot",
              u"thead", u"html"):
                #self.parser.parseError("unexpected-implied-end-tag-in-table",
                #  {"name": self.tree.openElements[-1].name})
                self.tree.openElements.pop()
            if self.tree.openElements[-1].name == u"html":
                assert self.parser.innerHTML
        clearStackToTableBodyContext.func_annotations = {}

        # the rest
        def processEOF(self):
            self.parser.phases[u"inTable"].processEOF()
        processEOF.func_annotations = {}

        def processSpaceCharacters(self, token):
            return self.parser.phases[u"inTable"].processSpaceCharacters(token)
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            return self.parser.phases[u"inTable"].processCharacters(token)
        processCharacters.func_annotations = {}

        def startTagTr(self, token):
            self.clearStackToTableBodyContext()
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inRow"]
        startTagTr.func_annotations = {}

        def startTagTableCell(self, token):
            self.parser.parseError(u"unexpected-cell-in-table-body", 
                                   {u"name": token[u"name"]})
            self.startTagTr(impliedTagToken(u"tr", u"StartTag"))
            return token
        startTagTableCell.func_annotations = {}

        def startTagTableOther(self, token):
            # XXX AT Any ideas on how to share this with endTagTable?
            if (self.tree.elementInScope(u"tbody", variant=u"table") or
                self.tree.elementInScope(u"thead", variant=u"table") or
                self.tree.elementInScope(u"tfoot", variant=u"table")):
                self.clearStackToTableBodyContext()
                self.endTagTableRowGroup(
                    impliedTagToken(self.tree.openElements[-1].name))
                return token
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        startTagTableOther.func_annotations = {}

        def startTagOther(self, token):
            return self.parser.phases[u"inTable"].processStartTag(token)
        startTagOther.func_annotations = {}

        def endTagTableRowGroup(self, token):
            if self.tree.elementInScope(token[u"name"], variant=u"table"):
                self.clearStackToTableBodyContext()
                self.tree.openElements.pop()
                self.parser.phase = self.parser.phases[u"inTable"]
            else:
                self.parser.parseError(u"unexpected-end-tag-in-table-body",
                  {u"name": token[u"name"]})
        endTagTableRowGroup.func_annotations = {}

        def endTagTable(self, token):
            if (self.tree.elementInScope(u"tbody", variant=u"table") or
                self.tree.elementInScope(u"thead", variant=u"table") or
                self.tree.elementInScope(u"tfoot", variant=u"table")):
                self.clearStackToTableBodyContext()
                self.endTagTableRowGroup(
                    impliedTagToken(self.tree.openElements[-1].name))
                return token
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        endTagTable.func_annotations = {}

        def endTagIgnore(self, token):
            self.parser.parseError(u"unexpected-end-tag-in-table-body",
              {u"name": token[u"name"]})
        endTagIgnore.func_annotations = {}

        def endTagOther(self, token):
            return self.parser.phases[u"inTable"].processEndTag(token)
        endTagOther.func_annotations = {}


    class InRowPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-row
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                ((u"td", u"th"), self.startTagTableCell),
                ((u"caption", u"col", u"colgroup", u"tbody", u"tfoot", u"thead",
                  u"tr"), self.startTagTableOther)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"tr", self.endTagTr),
                (u"table", self.endTagTable),
                ((u"tbody", u"tfoot", u"thead"), self.endTagTableRowGroup),
                ((u"body", u"caption", u"col", u"colgroup", u"html", u"td", u"th"),
                  self.endTagIgnore)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # helper methods (XXX unify this with other table helper methods)
        def clearStackToTableRowContext(self):
            while self.tree.openElements[-1].name not in (u"tr", u"html"):
                self.parser.parseError(u"unexpected-implied-end-tag-in-table-row",
                  {u"name": self.tree.openElements[-1].name})
                self.tree.openElements.pop()
        clearStackToTableRowContext.func_annotations = {}

        def ignoreEndTagTr(self):
            return not self.tree.elementInScope(u"tr", variant=u"table")
        ignoreEndTagTr.func_annotations = {}

        # the rest
        def processEOF(self):
            self.parser.phases[u"inTable"].processEOF()
        processEOF.func_annotations = {}

        def processSpaceCharacters(self, token):
            return self.parser.phases[u"inTable"].processSpaceCharacters(token)        
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            return self.parser.phases[u"inTable"].processCharacters(token)
        processCharacters.func_annotations = {}

        def startTagTableCell(self, token):
            self.clearStackToTableRowContext()
            self.tree.insertElement(token)
            self.parser.phase = self.parser.phases[u"inCell"]
            self.tree.activeFormattingElements.append(Marker)
        startTagTableCell.func_annotations = {}

        def startTagTableOther(self, token):
            ignoreEndTag = self.ignoreEndTagTr()
            self.endTagTr(impliedTagToken(u"tr"))
            # XXX how are we sure it's always ignored in the innerHTML case?
            if not ignoreEndTag:
                return token
        startTagTableOther.func_annotations = {}

        def startTagOther(self, token):
            return self.parser.phases[u"inTable"].processStartTag(token)
        startTagOther.func_annotations = {}

        def endTagTr(self, token):
            if not self.ignoreEndTagTr():
                self.clearStackToTableRowContext()
                self.tree.openElements.pop()
                self.parser.phase = self.parser.phases[u"inTableBody"]
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        endTagTr.func_annotations = {}

        def endTagTable(self, token):
            ignoreEndTag = self.ignoreEndTagTr()
            self.endTagTr(impliedTagToken(u"tr"))
            # Reprocess the current tag if the tr end tag was not ignored
            # XXX how are we sure it's always ignored in the innerHTML case?
            if not ignoreEndTag:
                return token
        endTagTable.func_annotations = {}

        def endTagTableRowGroup(self, token):
            if self.tree.elementInScope(token[u"name"], variant=u"table"):
                self.endTagTr(impliedTagToken(u"tr"))
                return token
            else:
                self.parser.parseError()
        endTagTableRowGroup.func_annotations = {}

        def endTagIgnore(self, token):
            self.parser.parseError(u"unexpected-end-tag-in-table-row",
                {u"name": token[u"name"]})
        endTagIgnore.func_annotations = {}

        def endTagOther(self, token):
            return self.parser.phases[u"inTable"].processEndTag(token)
        endTagOther.func_annotations = {}

    class InCellPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-cell
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                ((u"caption", u"col", u"colgroup", u"tbody", u"td", u"tfoot", u"th",
                  u"thead", u"tr"), self.startTagTableOther)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                ((u"td", u"th"), self.endTagTableCell),
                ((u"body", u"caption", u"col", u"colgroup", u"html"), self.endTagIgnore),
                ((u"table", u"tbody", u"tfoot", u"thead", u"tr"), self.endTagImply)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # helper
        def closeCell(self):
            if self.tree.elementInScope(u"td", variant=u"table"):
                self.endTagTableCell(impliedTagToken(u"td"))
            elif self.tree.elementInScope(u"th", variant=u"table"):
                self.endTagTableCell(impliedTagToken(u"th"))
        closeCell.func_annotations = {}

        # the rest
        def processEOF(self):
            self.parser.phases[u"inBody"].processEOF()
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            return self.parser.phases[u"inBody"].processCharacters(token)
        processCharacters.func_annotations = {}

        def startTagTableOther(self, token):
            if (self.tree.elementInScope(u"td", variant=u"table") or
                self.tree.elementInScope(u"th", variant=u"table")):
                self.closeCell()
                return token
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        startTagTableOther.func_annotations = {}

        def startTagOther(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagOther.func_annotations = {}

        def endTagTableCell(self, token):
            if self.tree.elementInScope(token[u"name"], variant=u"table"):
                self.tree.generateImpliedEndTags(token[u"name"])
                if self.tree.openElements[-1].name != token[u"name"]:
                    self.parser.parseError(u"unexpected-cell-end-tag",
                      {u"name": token[u"name"]})
                    while True:
                        node = self.tree.openElements.pop()
                        if node.name == token[u"name"]:
                            break
                else:
                    self.tree.openElements.pop()
                self.tree.clearActiveFormattingElements()
                self.parser.phase = self.parser.phases[u"inRow"]
            else:
                self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
        endTagTableCell.func_annotations = {}

        def endTagIgnore(self, token):
            self.parser.parseError(u"unexpected-end-tag", {u"name": token[u"name"]})
        endTagIgnore.func_annotations = {}

        def endTagImply(self, token):
            if self.tree.elementInScope(token[u"name"], variant=u"table"):
                self.closeCell()
                return token
            else:
                # sometimes innerHTML case
                self.parser.parseError()
        endTagImply.func_annotations = {}

        def endTagOther(self, token):
            return self.parser.phases[u"inBody"].processEndTag(token)
        endTagOther.func_annotations = {}

    class InSelectPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"option", self.startTagOption),
                (u"optgroup", self.startTagOptgroup),
                (u"select", self.startTagSelect),
                ((u"input", u"keygen", u"textarea"), self.startTagInput),
                (u"script", self.startTagScript)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"option", self.endTagOption),
                (u"optgroup", self.endTagOptgroup),
                (u"select", self.endTagSelect)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        # http://www.whatwg.org/specs/web-apps/current-work/#in-select
        def processEOF(self):
            if self.tree.openElements[-1].name != u"html":
                self.parser.parseError(u"eof-in-select")
            else:
                assert self.parser.innerHTML
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            if token[u"data"] == u"\u0000":
                return
            self.tree.insertText(token[u"data"])
        processCharacters.func_annotations = {}

        def startTagOption(self, token):
            # We need to imply </option> if <option> is the current node.
            if self.tree.openElements[-1].name == u"option":
                self.tree.openElements.pop()
            self.tree.insertElement(token)
        startTagOption.func_annotations = {}

        def startTagOptgroup(self, token):
            if self.tree.openElements[-1].name == u"option":
                self.tree.openElements.pop()
            if self.tree.openElements[-1].name == u"optgroup":
                self.tree.openElements.pop()
            self.tree.insertElement(token)
        startTagOptgroup.func_annotations = {}

        def startTagSelect(self, token):
            self.parser.parseError(u"unexpected-select-in-select")
            self.endTagSelect(impliedTagToken(u"select"))
        startTagSelect.func_annotations = {}

        def startTagInput(self, token):
            self.parser.parseError(u"unexpected-input-in-select")
            if self.tree.elementInScope(u"select", variant=u"select"):
                self.endTagSelect(impliedTagToken(u"select"))
                return token
            else:
                assert self.parser.innerHTML
        startTagInput.func_annotations = {}

        def startTagScript(self, token):
            return self.parser.phases[u"inHead"].processStartTag(token)
        startTagScript.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"unexpected-start-tag-in-select",
              {u"name": token[u"name"]})
        startTagOther.func_annotations = {}

        def endTagOption(self, token):
            if self.tree.openElements[-1].name == u"option":
                self.tree.openElements.pop()
            else:
                self.parser.parseError(u"unexpected-end-tag-in-select",
                  {u"name": u"option"})
        endTagOption.func_annotations = {}

        def endTagOptgroup(self, token):
            # </optgroup> implicitly closes <option>
            if (self.tree.openElements[-1].name == u"option" and
                self.tree.openElements[-2].name == u"optgroup"):
                self.tree.openElements.pop()
            # It also closes </optgroup>
            if self.tree.openElements[-1].name == u"optgroup":
                self.tree.openElements.pop()
            # But nothing else
            else:
                self.parser.parseError(u"unexpected-end-tag-in-select",
                  {u"name": u"optgroup"})
        endTagOptgroup.func_annotations = {}

        def endTagSelect(self, token):
            if self.tree.elementInScope(u"select", variant=u"select"):
                node = self.tree.openElements.pop()
                while node.name != u"select":
                    node = self.tree.openElements.pop()
                self.parser.resetInsertionMode()
            else:
                # innerHTML case
                assert self.parser.innerHTML
                self.parser.parseError()
        endTagSelect.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag-in-select",
              {u"name": token[u"name"]})
        endTagOther.func_annotations = {}


    class InSelectInTablePhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                ((u"caption", u"table", u"tbody", u"tfoot", u"thead", u"tr", u"td", u"th"),
                 self.startTagTable)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                ((u"caption", u"table", u"tbody", u"tfoot", u"thead", u"tr", u"td", u"th"),
                 self.endTagTable)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            self.parser.phases[u"inSelect"].processEOF()
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            return self.parser.phases[u"inSelect"].processCharacters(token)
        processCharacters.func_annotations = {}

        def startTagTable(self, token):
            self.parser.parseError(u"unexpected-table-element-start-tag-in-select-in-table", {u"name": token[u"name"]})
            self.endTagOther(impliedTagToken(u"select"))
            return token
        startTagTable.func_annotations = {}

        def startTagOther(self, token):
            return self.parser.phases[u"inSelect"].processStartTag(token)
        startTagOther.func_annotations = {}

        def endTagTable(self, token):
            self.parser.parseError(u"unexpected-table-element-end-tag-in-select-in-table", {u"name": token[u"name"]})
            if self.tree.elementInScope(token[u"name"], variant=u"table"):
                self.endTagOther(impliedTagToken(u"select"))
                return token
        endTagTable.func_annotations = {}

        def endTagOther(self, token):
            return self.parser.phases[u"inSelect"].processEndTag(token)
        endTagOther.func_annotations = {}


    class InForeignContentPhase(Phase):
        breakoutElements = frozenset([u"b", u"big", u"blockquote", u"body", u"br", 
                                      u"center", u"code", u"dd", u"div", u"dl", u"dt",
                                      u"em", u"embed", u"h1", u"h2", u"h3", 
                                      u"h4", u"h5", u"h6", u"head", u"hr", u"i", u"img",
                                      u"li", u"listing", u"menu", u"meta", u"nobr", 
                                      u"ol", u"p", u"pre", u"ruby", u"s",  u"small", 
                                      u"span", u"strong", u"strike",  u"sub", u"sup", 
                                      u"table", u"tt", u"u", u"ul", u"var"])
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)
        __init__.func_annotations = {}

        def adjustSVGTagNames(self, token):
            replacements = {u"altglyph":u"altGlyph",
                            u"altglyphdef":u"altGlyphDef",
                            u"altglyphitem":u"altGlyphItem",
                            u"animatecolor":u"animateColor",
                            u"animatemotion":u"animateMotion",
                            u"animatetransform":u"animateTransform",
                            u"clippath":u"clipPath",
                            u"feblend":u"feBlend",
                            u"fecolormatrix":u"feColorMatrix",
                            u"fecomponenttransfer":u"feComponentTransfer",
                            u"fecomposite":u"feComposite",
                            u"feconvolvematrix":u"feConvolveMatrix",
                            u"fediffuselighting":u"feDiffuseLighting",
                            u"fedisplacementmap":u"feDisplacementMap",
                            u"fedistantlight":u"feDistantLight",
                            u"feflood":u"feFlood",
                            u"fefunca":u"feFuncA",
                            u"fefuncb":u"feFuncB",
                            u"fefuncg":u"feFuncG",
                            u"fefuncr":u"feFuncR",
                            u"fegaussianblur":u"feGaussianBlur",
                            u"feimage":u"feImage",
                            u"femerge":u"feMerge",
                            u"femergenode":u"feMergeNode",
                            u"femorphology":u"feMorphology",
                            u"feoffset":u"feOffset",
                            u"fepointlight":u"fePointLight",
                            u"fespecularlighting":u"feSpecularLighting",
                            u"fespotlight":u"feSpotLight",
                            u"fetile":u"feTile",
                            u"feturbulence":u"feTurbulence",
                            u"foreignobject":u"foreignObject",
                            u"glyphref":u"glyphRef",
                            u"lineargradient":u"linearGradient",
                            u"radialgradient":u"radialGradient",
                            u"textpath":u"textPath"}

            if token[u"name"] in replacements:
                token[u"name"] = replacements[token[u"name"]]
        adjustSVGTagNames.func_annotations = {}

        def processCharacters(self, token):
            if token[u"data"] == u"\u0000":
                token[u"data"] = u"\uFFFD"
            elif (self.parser.framesetOK and 
                  any(char not in spaceCharacters for char in token[u"data"])):
                self.parser.framesetOK = False
            Phase.processCharacters(self, token)
        processCharacters.func_annotations = {}

        def processStartTag(self, token):
            currentNode = self.tree.openElements[-1]
            if (token[u"name"] in self.breakoutElements or
                (token[u"name"] == u"font" and
                 set(token[u"data"].keys()) & set([u"color", u"face", u"size"]))):
                self.parser.parseError(u"unexpected-html-element-in-foreign-content",
                                       token[u"name"])
                while (self.tree.openElements[-1].namespace !=
                       self.tree.defaultNamespace and 
                       not self.parser.isHTMLIntegrationPoint(self.tree.openElements[-1]) and
                       not self.parser.isMathMLTextIntegrationPoint(self.tree.openElements[-1])):
                    self.tree.openElements.pop()
                return token

            else:
                if currentNode.namespace == namespaces[u"mathml"]:
                    self.parser.adjustMathMLAttributes(token)
                elif currentNode.namespace == namespaces[u"svg"]:
                    self.adjustSVGTagNames(token)
                    self.parser.adjustSVGAttributes(token)
                self.parser.adjustForeignAttributes(token)
                token[u"namespace"] = currentNode.namespace
                self.tree.insertElement(token)
                if token[u"selfClosing"]:
                    self.tree.openElements.pop()
                    token[u"selfClosingAcknowledged"] = True
        processStartTag.func_annotations = {}

        def processEndTag(self, token):
            nodeIndex = len(self.tree.openElements) - 1
            node = self.tree.openElements[-1]
            if node.name != token[u"name"]:
                self.parser.parseError(u"unexpected-end-tag", token[u"name"])

            while True:
                if node.name.translate(asciiUpper2Lower) == token[u"name"]:
                    #XXX this isn't in the spec but it seems necessary
                    if self.parser.phase == self.parser.phases[u"inTableText"]:
                        self.parser.phase.flushCharacters()
                        self.parser.phase = self.parser.phase.originalPhase
                    while self.tree.openElements.pop() != node:
                        assert self.tree.openElements
                    new_token = None
                    break
                nodeIndex -= 1

                node = self.tree.openElements[nodeIndex]
                if node.namespace != self.tree.defaultNamespace:
                    continue
                else:
                    new_token = self.parser.phase.processEndTag(token)
                    break
            return new_token
        processEndTag.func_annotations = {}


    class AfterBodyPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                    (u"html", self.startTagHtml)
                    ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([(u"html", self.endTagHtml)])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            #Stop parsing
            pass
        processEOF.func_annotations = {}

        def processComment(self, token):
            # This is needed because data is to be appended to the <html> element
            # here and not to whatever is currently open.
            self.tree.insertComment(token, self.tree.openElements[0])
        processComment.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"unexpected-char-after-body")
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"unexpected-start-tag-after-body",
              {u"name": token[u"name"]})
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        startTagOther.func_annotations = {}

        def endTagHtml(self,name):
            if self.parser.innerHTML:
                self.parser.parseError(u"unexpected-end-tag-after-body-innerhtml")
            else:
                self.parser.phase = self.parser.phases[u"afterAfterBody"]
        endTagHtml.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag-after-body",
              {u"name": token[u"name"]})
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        endTagOther.func_annotations = {}

    class InFramesetPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#in-frameset
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"frameset", self.startTagFrameset),
                (u"frame", self.startTagFrame),
                (u"noframes", self.startTagNoframes)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"frameset", self.endTagFrameset)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            if self.tree.openElements[-1].name != u"html":
                self.parser.parseError(u"eof-in-frameset")
            else:
                assert self.parser.innerHTML
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"unexpected-char-in-frameset")
        processCharacters.func_annotations = {}

        def startTagFrameset(self, token):
            self.tree.insertElement(token)
        startTagFrameset.func_annotations = {}

        def startTagFrame(self, token):
            self.tree.insertElement(token)
            self.tree.openElements.pop()
        startTagFrame.func_annotations = {}

        def startTagNoframes(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagNoframes.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"unexpected-start-tag-in-frameset",
              {u"name": token[u"name"]})
        startTagOther.func_annotations = {}

        def endTagFrameset(self, token):
            if self.tree.openElements[-1].name == u"html":
                # innerHTML case
                self.parser.parseError(u"unexpected-frameset-in-frameset-innerhtml")
            else:
                self.tree.openElements.pop()
            if (not self.parser.innerHTML and
                self.tree.openElements[-1].name != u"frameset"):
                # If we're not in innerHTML mode and the the current node is not a
                # "frameset" element (anymore) then switch.
                self.parser.phase = self.parser.phases[u"afterFrameset"]
        endTagFrameset.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag-in-frameset",
              {u"name": token[u"name"]})
        endTagOther.func_annotations = {}


    class AfterFramesetPhase(Phase):
        # http://www.whatwg.org/specs/web-apps/current-work/#after3
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"noframes", self.startTagNoframes)
            ])
            self.startTagHandler.default = self.startTagOther

            self.endTagHandler = utils.MethodDispatcher([
                (u"html", self.endTagHtml)
            ])
            self.endTagHandler.default = self.endTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            #Stop parsing
            pass
        processEOF.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"unexpected-char-after-frameset")
        processCharacters.func_annotations = {}

        def startTagNoframes(self, token):
            return self.parser.phases[u"inHead"].processStartTag(token)
        startTagNoframes.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"unexpected-start-tag-after-frameset",
              {u"name": token[u"name"]})
        startTagOther.func_annotations = {}

        def endTagHtml(self, token):
            self.parser.phase = self.parser.phases[u"afterAfterFrameset"]
        endTagHtml.func_annotations = {}

        def endTagOther(self, token):
            self.parser.parseError(u"unexpected-end-tag-after-frameset",
              {u"name": token[u"name"]})
        endTagOther.func_annotations = {}


    class AfterAfterBodyPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml)
            ])
            self.startTagHandler.default = self.startTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            pass
        processEOF.func_annotations = {}

        def processComment(self, token):
            self.tree.insertComment(token, self.tree.document)
        processComment.func_annotations = {}

        def processSpaceCharacters(self, token):
            return self.parser.phases[u"inBody"].processSpaceCharacters(token)
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"expected-eof-but-got-char")
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"expected-eof-but-got-start-tag",
              {u"name": token[u"name"]})
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        startTagOther.func_annotations = {}

        def processEndTag(self, token):
            self.parser.parseError(u"expected-eof-but-got-end-tag",
              {u"name": token[u"name"]})
            self.parser.phase = self.parser.phases[u"inBody"]
            return token
        processEndTag.func_annotations = {}

    class AfterAfterFramesetPhase(Phase):
        def __init__(self, parser, tree):
            Phase.__init__(self, parser, tree)

            self.startTagHandler = utils.MethodDispatcher([
                (u"html", self.startTagHtml),
                (u"noframes", self.startTagNoFrames)
            ])
            self.startTagHandler.default = self.startTagOther
        __init__.func_annotations = {}

        def processEOF(self):
            pass
        processEOF.func_annotations = {}

        def processComment(self, token):
            self.tree.insertComment(token, self.tree.document)
        processComment.func_annotations = {}

        def processSpaceCharacters(self, token):
            return self.parser.phases[u"inBody"].processSpaceCharacters(token)
        processSpaceCharacters.func_annotations = {}

        def processCharacters(self, token):
            self.parser.parseError(u"expected-eof-but-got-char")
        processCharacters.func_annotations = {}

        def startTagHtml(self, token):
            return self.parser.phases[u"inBody"].processStartTag(token)
        startTagHtml.func_annotations = {}

        def startTagNoFrames(self, token):
            return self.parser.phases[u"inHead"].processStartTag(token)
        startTagNoFrames.func_annotations = {}

        def startTagOther(self, token):
            self.parser.parseError(u"expected-eof-but-got-start-tag",
              {u"name": token[u"name"]})
        startTagOther.func_annotations = {}

        def processEndTag(self, token):
            self.parser.parseError(u"expected-eof-but-got-end-tag",
              {u"name": token[u"name"]})
        processEndTag.func_annotations = {}


    return {
        u"initial": InitialPhase,
        u"beforeHtml": BeforeHtmlPhase,
        u"beforeHead": BeforeHeadPhase,
        u"inHead": InHeadPhase,
        # XXX "inHeadNoscript": InHeadNoScriptPhase,
        u"afterHead": AfterHeadPhase,
        u"inBody": InBodyPhase,
        u"text": TextPhase,
        u"inTable": InTablePhase,
        u"inTableText": InTableTextPhase,
        u"inCaption": InCaptionPhase,
        u"inColumnGroup": InColumnGroupPhase,
        u"inTableBody": InTableBodyPhase,
        u"inRow": InRowPhase,
        u"inCell": InCellPhase,
        u"inSelect": InSelectPhase,
        u"inSelectInTable": InSelectInTablePhase,
        u"inForeignContent": InForeignContentPhase,
        u"afterBody": AfterBodyPhase,
        u"inFrameset": InFramesetPhase,
        u"afterFrameset": AfterFramesetPhase,
        u"afterAfterBody": AfterAfterBodyPhase,
        u"afterAfterFrameset": AfterAfterFramesetPhase,
        # XXX after after frameset
        }
getPhases.func_annotations = {}

def impliedTagToken(name, type=u"EndTag", attributes = None, 
                    selfClosing = False):
    if attributes is None:
        attributes = {}
    return {u"type":tokenTypes[type], u"name":unicode(name), u"data":attributes,
            u"selfClosing":selfClosing}
impliedTagToken.func_annotations = {}

class ParseError(Exception):
    u"""Error in parsed document"""
    pass
