from __future__ import absolute_import
try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset
try:
    from collections import deque
except ImportError:
    from .utils import deque
    
from .constants import spaceCharacters
from .constants import entitiesWindows1252, entities
from .constants import asciiLowercase, asciiLetters, asciiUpper2Lower
from .constants import digits, hexDigits, EOF
from .constants import tokenTypes, tagTokenTypes
from .constants import replacementCharacters

from .inputstream import HTMLInputStream

# Group entities by their first character, for faster lookups
entitiesByFirstChar = {}
for e in entities:
    entitiesByFirstChar.setdefault(e[0], []).append(e)

class HTMLTokenizer(object):
    u""" This class takes care of tokenizing HTML.

    * self.currentToken
      Holds the token that is currently being processed.

    * self.state
      Holds a reference to the method to be invoked... XXX

    * self.stream
      Points to HTMLInputStream object.
    """

    def __init__(self, stream, encoding=None, parseMeta=True, useChardet=True,
                 lowercaseElementName=True, lowercaseAttrName=True, parser=None):

        self.stream = HTMLInputStream(stream, encoding, parseMeta, useChardet)
        self.parser = parser

        #Perform case conversions?
        self.lowercaseElementName = lowercaseElementName
        self.lowercaseAttrName = lowercaseAttrName
        
        # Setup the initial tokenizer state
        self.escapeFlag = False
        self.lastFourChars = []
        self.state = self.dataState
        self.escape = False

        # The current token being created
        self.currentToken = None
        super(HTMLTokenizer, self).__init__()
    __init__.func_annotations = {}

    def __iter__(self):
        u""" This is where the magic happens.

        We do our usually processing through the states and when we have a token
        to return we yield the token which pauses processing until the next token
        is requested.
        """
        self.tokenQueue = deque([])
        # Start processing. When EOF is reached self.state will return False
        # instead of True and the loop will terminate.
        while self.state():
            while self.stream.errors:
                yield {u"type": tokenTypes[u"ParseError"], u"data": self.stream.errors.pop(0)}
            while self.tokenQueue:
                yield self.tokenQueue.popleft()
    __iter__.func_annotations = {}

    def consumeNumberEntity(self, isHex):
        u"""This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.tokenQueue.append({"type": tokenTypes["ParseError"]}) is invoked.
        """

        allowed = digits
        radix = 10
        if isHex:
            allowed = hexDigits
            radix = 16

        charStack = []

        # Consume all the characters that are in range while making sure we
        # don't hit an EOF.
        c = self.stream.char()
        while c in allowed and c is not EOF:
            charStack.append(c)
            c = self.stream.char()

        # Convert the set of characters consumed to an int.
        charAsInt = int(u"".join(charStack), radix)

        # Certain characters get replaced with others
        if charAsInt in replacementCharacters:
            char = replacementCharacters[charAsInt]
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"illegal-codepoint-for-numeric-entity",
              u"datavars": {u"charAsInt": charAsInt}})
        elif ((0xD800 <= charAsInt <= 0xDFFF) or 
              (charAsInt > 0x10FFFF)):
            char = u"\uFFFD"
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"illegal-codepoint-for-numeric-entity",
              u"datavars": {u"charAsInt": charAsInt}})
        else:
            #Should speed up this check somehow (e.g. move the set to a constant)
            if ((0x0001 <= charAsInt <= 0x0008) or 
                (0x000E <= charAsInt <= 0x001F) or 
                (0x007F  <= charAsInt <= 0x009F) or
                (0xFDD0  <= charAsInt <= 0xFDEF) or 
                charAsInt in frozenset([0x000B, 0xFFFE, 0xFFFF, 0x1FFFE, 
                                        0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE,
                                        0x3FFFF, 0x4FFFE, 0x4FFFF, 0x5FFFE, 
                                        0x5FFFF, 0x6FFFE, 0x6FFFF, 0x7FFFE,
                                        0x7FFFF, 0x8FFFE, 0x8FFFF, 0x9FFFE,
                                        0x9FFFF, 0xAFFFE, 0xAFFFF, 0xBFFFE, 
                                        0xBFFFF, 0xCFFFE, 0xCFFFF, 0xDFFFE, 
                                        0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE, 
                                        0xFFFFF, 0x10FFFE, 0x10FFFF])):
                self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                        u"data":
                                            u"illegal-codepoint-for-numeric-entity",
                                        u"datavars": {u"charAsInt": charAsInt}})
            try:
                # Try/except needed as UCS-2 Python builds' unichar only works
                # within the BMP.
                char = unichr(charAsInt)
            except ValueError:
                char = eval(u"u'\\U%08x'" % charAsInt)

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        if c != u";":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"numeric-entity-without-semicolon"})
            self.stream.unget(c)

        return char
    consumeNumberEntity.func_annotations = {}

    def consumeEntity(self, allowedChar=None, fromAttribute=False):
        # Initialise to the default output for when no entity is matched
        output = u"&"

        charStack = [self.stream.char()]
        if (charStack[0] in spaceCharacters or charStack[0] in (EOF, u"<", u"&") 
            or (allowedChar is not None and allowedChar == charStack[0])):
            self.stream.unget(charStack[0])

        elif charStack[0] == u"#":
            # Read the next character to see if it's hex or decimal
            hex = False
            charStack.append(self.stream.char())
            if charStack[-1] in (u"x", u"X"):
                hex = True
                charStack.append(self.stream.char())

            # charStack[-1] should be the first digit
            if (hex and charStack[-1] in hexDigits) \
             or (not hex and charStack[-1] in digits):
                # At least one digit found, so consume the whole number
                self.stream.unget(charStack[-1])
                output = self.consumeNumberEntity(hex)
            else:
                # No digits found
                self.tokenQueue.append({u"type": tokenTypes[u"ParseError"],
                    u"data": u"expected-numeric-entity"})
                self.stream.unget(charStack.pop())
                output = u"&" + u"".join(charStack)

        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".
            #
            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer matches.
            filteredEntityList = entitiesByFirstChar.get(charStack[0], [])

            def entitiesStartingWith(name):
                return [e for e in filteredEntityList if e.startswith(name)]
            entitiesStartingWith.func_annotations = {}

            while (charStack[-1] is not EOF):
                filteredEntityList = entitiesStartingWith(u"".join(charStack))
                if not filteredEntityList:
                    break
                charStack.append(self.stream.char())

            # At this point we have a string that starts with some characters
            # that may match an entity
            entityName = None

            # Try to find the longest entity the string will match to take care
            # of &noti for instance.
            for entityLength in xrange(len(charStack)-1, 1, -1):
                possibleEntityName = u"".join(charStack[:entityLength])
                if possibleEntityName in entities:
                    entityName = possibleEntityName
                    break

            if entityName is not None:
                if entityName[-1] != u";":
                    self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
                      u"named-entity-without-semicolon"})
                if (entityName[-1] != u";" and fromAttribute and
                    (charStack[entityLength] in asciiLetters or
                     charStack[entityLength] in digits or
                    charStack[entityLength] == u"=")):
                    self.stream.unget(charStack.pop())
                    output = u"&" + u"".join(charStack)
                else:
                    output = entities[entityName]
                    self.stream.unget(charStack.pop())
                    output += u"".join(charStack[entityLength:])
            else:
                self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
                  u"expected-named-entity"})
                self.stream.unget(charStack.pop())
                output = u"&" + u"".join(charStack)

        if fromAttribute:
            self.currentToken[u"data"][-1][1] += output
        else:
            if output in spaceCharacters:
                tokenType = u"SpaceCharacters"
            else:
                tokenType = u"Characters"
            self.tokenQueue.append({u"type": tokenTypes[tokenType], u"data": output})
    consumeEntity.func_annotations = {}

    def processEntityInAttribute(self, allowedChar):
        u"""This method replaces the need for "entityInAttributeValueState".
        """
        self.consumeEntity(allowedChar=allowedChar, fromAttribute=True)
    processEntityInAttribute.func_annotations = {}

    def emitCurrentToken(self):
        u"""This method is a generic handler for emitting the tags. It also sets
        the state to "data" because that's what's needed after a token has been
        emitted.
        """
        token = self.currentToken
        # Add token to the queue to be yielded
        if (token[u"type"] in tagTokenTypes):
            if self.lowercaseElementName:
                token[u"name"] = token[u"name"].translate(asciiUpper2Lower)
            if token[u"type"] == tokenTypes[u"EndTag"]:
                if token[u"data"]:
                    self.tokenQueue.append({u"type":tokenTypes[u"ParseError"],
                                            u"data":u"attributes-in-end-tag"})
                if token[u"selfClosing"]:
                    self.tokenQueue.append({u"type":tokenTypes[u"ParseError"],
                                            u"data":u"self-closing-flag-on-end-tag"})
        self.tokenQueue.append(token)
        self.state = self.dataState
    emitCurrentToken.func_annotations = {}


    # Below are the various tokenizer states worked out.

    def dataState(self):
        data = self.stream.char()
        if data == u"&":
            self.state = self.entityDataState
        elif data == u"<":
            self.state = self.tagOpenState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data":u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\u0000"})
        elif data is EOF:
            # Tokenization ends.
            return False
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append({u"type": tokenTypes[u"SpaceCharacters"], u"data":
              data + self.stream.charsUntil(spaceCharacters, True)})
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil((u"&", u"<", u"\u0000"))
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
              data + chars})
        return True
    dataState.func_annotations = {}

    def entityDataState(self):
        self.consumeEntity()
        self.state = self.dataState
        return True
    entityDataState.func_annotations = {}
    
    def rcdataState(self):
        data = self.stream.char()
        if data == u"&":
            self.state = self.characterReferenceInRcdata
        elif data == u"<":
            self.state = self.rcdataLessThanSignState
        elif data == EOF:
            # Tokenization ends.
            return False
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append({u"type": tokenTypes[u"SpaceCharacters"], u"data":
              data + self.stream.charsUntil(spaceCharacters, True)})
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil((u"&", u"<"))
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
              data + chars})
        return True
    rcdataState.func_annotations = {}

    def characterReferenceInRcdata(self):
        self.consumeEntity()
        self.state = self.rcdataState
        return True
    characterReferenceInRcdata.func_annotations = {}
    
    def rawtextState(self):
        data = self.stream.char()
        if data == u"<":
            self.state = self.rawtextLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil((u"<", u"\u0000"))
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
              data + chars})
        return True
    rawtextState.func_annotations = {}
    
    def scriptDataState(self):
        data = self.stream.char()
        if data == u"<":
            self.state = self.scriptDataLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil((u"<", u"\u0000"))
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
              data + chars})
        return True
    scriptDataState.func_annotations = {}
    
    def plaintextState(self):
        data = self.stream.char()
        if data == EOF:
            # Tokenization ends.
            return False
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
                                    data + self.stream.charsUntil(u"\u0000")})
        return True
    plaintextState.func_annotations = {}

    def tagOpenState(self):
        data = self.stream.char()
        if data == u"!":
            self.state = self.markupDeclarationOpenState
        elif data == u"/":
            self.state = self.closeTagOpenState
        elif data in asciiLetters:
            self.currentToken = {u"type": tokenTypes[u"StartTag"], 
                                 u"name": data, u"data": [],
                                 u"selfClosing": False,
                                 u"selfClosingAcknowledged": False}
            self.state = self.tagNameState
        elif data == u">":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-tag-name-but-got-right-bracket"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<>"})
            self.state = self.dataState
        elif data == u"?":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-tag-name-but-got-question-mark"})
            self.stream.unget(data)
            self.state = self.bogusCommentState
        else:
            # XXX
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-tag-name"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.stream.unget(data)
            self.state = self.dataState
        return True
    tagOpenState.func_annotations = {}

    def closeTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.currentToken = {u"type": tokenTypes[u"EndTag"], u"name": data,
                                 u"data": [], u"selfClosing":False}
            self.state = self.tagNameState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-closing-tag-but-got-right-bracket"})
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-closing-tag-but-got-eof"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"</"})
            self.state = self.dataState
        else:
            # XXX data can be _'_...
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-closing-tag-but-got-char",
              u"datavars": {u"data": data}})
            self.stream.unget(data)
            self.state = self.bogusCommentState
        return True
    closeTagOpenState.func_annotations = {}

    def tagNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == u">":
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-tag-name"})
            self.state = self.dataState
        elif data == u"/":
            self.state = self.selfClosingStartTagState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"name"] += u"\uFFFD"
        else:
            self.currentToken[u"name"] += data
            # (Don't use charsUntil here, because tag names are
            # very short and it's faster to not do anything fancy)
        return True
    tagNameState.func_annotations = {}
    
    def rcdataLessThanSignState(self):
        data = self.stream.char()
        if data == u"/":
            self.temporaryBuffer = u""
            self.state = self.rcdataEndTagOpenState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.stream.unget(data)
            self.state = self.rcdataState
        return True
    rcdataLessThanSignState.func_annotations = {}
    
    def rcdataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.rcdataEndTagNameState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"</"})
            self.stream.unget(data)
            self.state = self.rcdataState
        return True
    rcdataEndTagOpenState.func_annotations = {}
    
    def rcdataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken[u"name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.beforeAttributeNameState
        elif data == u"/" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.selfClosingStartTagState
        elif data == u">" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"],
                                    u"data": u"</" + self.temporaryBuffer})
            self.stream.unget(data)
            self.state = self.rcdataState
        return True
    rcdataEndTagNameState.func_annotations = {}
    
    def rawtextLessThanSignState(self):
        data = self.stream.char()
        if data == u"/":
            self.temporaryBuffer = u""
            self.state = self.rawtextEndTagOpenState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.stream.unget(data)
            self.state = self.rawtextState
        return True
    rawtextLessThanSignState.func_annotations = {}
    
    def rawtextEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.rawtextEndTagNameState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"</"})
            self.stream.unget(data)
            self.state = self.rawtextState
        return True
    rawtextEndTagOpenState.func_annotations = {}
    
    def rawtextEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken[u"name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.beforeAttributeNameState
        elif data == u"/" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.selfClosingStartTagState
        elif data == u">" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"],
                                    u"data": u"</" + self.temporaryBuffer})
            self.stream.unget(data)
            self.state = self.rawtextState
        return True
    rawtextEndTagNameState.func_annotations = {}
    
    def scriptDataLessThanSignState(self):
        data = self.stream.char()
        if data == u"/":
            self.temporaryBuffer = u""
            self.state = self.scriptDataEndTagOpenState
        elif data == u"!":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<!"})
            self.state = self.scriptDataEscapeStartState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True
    scriptDataLessThanSignState.func_annotations = {}
    
    def scriptDataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.scriptDataEndTagNameState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"</"})
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True
    scriptDataEndTagOpenState.func_annotations = {}
    
    def scriptDataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken[u"name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.beforeAttributeNameState
        elif data == u"/" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.selfClosingStartTagState
        elif data == u">" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"],
                                    u"data": u"</" + self.temporaryBuffer})
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True
    scriptDataEndTagNameState.func_annotations = {}
    
    def scriptDataEscapeStartState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataEscapeStartDashState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True
    scriptDataEscapeStartState.func_annotations = {}
    
    def scriptDataEscapeStartDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataEscapedDashDashState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True
    scriptDataEscapeStartDashState.func_annotations = {}
    
    def scriptDataEscapedState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataEscapedDashState
        elif data == u"<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        elif data == EOF:
            self.state = self.dataState
        else:
            chars = self.stream.charsUntil((u"<", u"-", u"\u0000"))
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": 
              data + chars})
        return True
    scriptDataEscapedState.func_annotations = {}
    
    def scriptDataEscapedDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataEscapedDashDashState
        elif data == u"<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
            self.state = self.scriptDataEscapedState
        elif data == EOF:
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.state = self.scriptDataEscapedState
        return True
    scriptDataEscapedDashState.func_annotations = {}
    
    def scriptDataEscapedDashDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
        elif data == u"<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u">"})
            self.state = self.scriptDataState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
            self.state = self.scriptDataEscapedState
        elif data == EOF:
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.state = self.scriptDataEscapedState
        return True
    scriptDataEscapedDashDashState.func_annotations = {}
    
    def scriptDataEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == u"/":
            self.temporaryBuffer = u""
            self.state = self.scriptDataEscapedEndTagOpenState
        elif data in asciiLetters:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<" + data})
            self.temporaryBuffer = data
            self.state = self.scriptDataDoubleEscapeStartState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True
    scriptDataEscapedLessThanSignState.func_annotations = {}
    
    def scriptDataEscapedEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer = data
            self.state = self.scriptDataEscapedEndTagNameState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"</"})
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True
    scriptDataEscapedEndTagOpenState.func_annotations = {}
    
    def scriptDataEscapedEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken[u"name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.beforeAttributeNameState
        elif data == u"/" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.state = self.selfClosingStartTagState
        elif data == u">" and appropriate:
            self.currentToken = {u"type": tokenTypes[u"EndTag"],
                                 u"name": self.temporaryBuffer,
                                 u"data": [], u"selfClosing":False}
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"],
                                    u"data": u"</" + self.temporaryBuffer})
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True
    scriptDataEscapedEndTagNameState.func_annotations = {}
    
    def scriptDataDoubleEscapeStartState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset((u"/", u">"))):
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            if self.temporaryBuffer.lower() == u"script":
                self.state = self.scriptDataDoubleEscapedState
            else:
                self.state = self.scriptDataEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True
    scriptDataDoubleEscapeStartState.func_annotations = {}
    
    def scriptDataDoubleEscapedState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataDoubleEscapedDashState
        elif data == u"<":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
        elif data == EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-script-in-script"})
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
        return True
    scriptDataDoubleEscapedState.func_annotations = {}
    
    def scriptDataDoubleEscapedDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
            self.state = self.scriptDataDoubleEscapedDashDashState
        elif data == u"<":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
            self.state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-script-in-script"})
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.state = self.scriptDataDoubleEscapedState
        return True
    scriptDataDoubleEscapedDashState.func_annotations = {}
    
    def scriptDataDoubleEscapedDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"-"})
        elif data == u"<":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"<"})
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u">"})
            self.state = self.scriptDataState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": u"\uFFFD"})
            self.state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-script-in-script"})
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.state = self.scriptDataDoubleEscapedState
        return True
    scriptDataDoubleEscapedDashState.func_annotations = {}
    
    def scriptDataDoubleEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == u"/":
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": u"/"})
            self.temporaryBuffer = u""
            self.state = self.scriptDataDoubleEscapeEndState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataDoubleEscapedState
        return True
    scriptDataDoubleEscapedLessThanSignState.func_annotations = {}
    
    def scriptDataDoubleEscapeEndState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset((u"/", u">"))):
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            if self.temporaryBuffer.lower() == u"script":
                self.state = self.scriptDataEscapedState
            else:
                self.state = self.scriptDataDoubleEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], u"data": data})
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self.state = self.scriptDataDoubleEscapedState
        return True
    scriptDataDoubleEscapeEndState.func_annotations = {}

    def beforeAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data in asciiLetters:
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"/":
            self.state = self.selfClosingStartTagState
        elif data in (u"'", u'"', u"=", u"<"):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"invalid-character-in-attribute-name"})
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"].append([u"\uFFFD", u""])
            self.state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-attribute-name-but-got-eof"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        return True
    beforeAttributeNameState.func_annotations = {}

    def attributeNameState(self):
        data = self.stream.char()
        leavingThisState = True
        emitToken = False
        if data == u"=":
            self.state = self.beforeAttributeValueState
        elif data in asciiLetters:
            self.currentToken[u"data"][-1][0] += data +\
              self.stream.charsUntil(asciiLetters, True)
            leavingThisState = False
        elif data == u">":
            # XXX If we emit here the attributes are converted to a dict
            # without being checked and when the code below runs we error
            # because data is a dict not a list
            emitToken = True
        elif data in spaceCharacters:
            self.state = self.afterAttributeNameState
        elif data == u"/":
            self.state = self.selfClosingStartTagState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"][-1][0] += u"\uFFFD"
            leavingThisState = False
        elif data in (u"'", u'"', u"<"):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data":
                                        u"invalid-character-in-attribute-name"})
            self.currentToken[u"data"][-1][0] += data
            leavingThisState = False
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"eof-in-attribute-name"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"][-1][0] += data
            leavingThisState = False

        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            if self.lowercaseAttrName:
                self.currentToken[u"data"][-1][0] = (
                    self.currentToken[u"data"][-1][0].translate(asciiUpper2Lower))
            for name, value in self.currentToken[u"data"][:-1]:
                if self.currentToken[u"data"][-1][0] == name:
                    self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
                      u"duplicate-attribute"})
                    break
            # XXX Fix for above XXX
            if emitToken:
                self.emitCurrentToken()
        return True
    attributeNameState.func_annotations = {}

    def afterAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == u"=":
            self.state = self.beforeAttributeValueState
        elif data == u">":
            self.emitCurrentToken()
        elif data in asciiLetters:
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        elif data == u"/":
            self.state = self.selfClosingStartTagState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"].append([u"\uFFFD", u""])
            self.state = self.attributeNameState
        elif data in (u"'", u'"', u"<"):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"invalid-character-after-attribute-name"})
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-end-of-tag-but-got-eof"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"].append([data, u""])
            self.state = self.attributeNameState
        return True
    afterAttributeNameState.func_annotations = {}

    def beforeAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == u"\"":
            self.state = self.attributeValueDoubleQuotedState
        elif data == u"&":
            self.state = self.attributeValueUnQuotedState
            self.stream.unget(data);
        elif data == u"'":
            self.state = self.attributeValueSingleQuotedState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-attribute-value-but-got-right-bracket"})
            self.emitCurrentToken()
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"][-1][1] += u"\uFFFD"
            self.state = self.attributeValueUnQuotedState
        elif data in (u"=", u"<", u"`"):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"equals-in-unquoted-attribute-value"})
            self.currentToken[u"data"][-1][1] += data
            self.state = self.attributeValueUnQuotedState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-attribute-value-but-got-eof"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"][-1][1] += data
            self.state = self.attributeValueUnQuotedState
        return True
    beforeAttributeValueState.func_annotations = {}

    def attributeValueDoubleQuotedState(self):
        data = self.stream.char()
        if data == u"\"":
            self.state = self.afterAttributeValueState
        elif data == u"&":
            self.processEntityInAttribute(u'"')
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"][-1][1] += u"\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-attribute-value-double-quote"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"][-1][1] += data +\
              self.stream.charsUntil((u"\"", u"&"))
        return True
    attributeValueDoubleQuotedState.func_annotations = {}

    def attributeValueSingleQuotedState(self):
        data = self.stream.char()
        if data == u"'":
            self.state = self.afterAttributeValueState
        elif data == u"&":
            self.processEntityInAttribute(u"'")
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"][-1][1] += u"\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-attribute-value-single-quote"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"][-1][1] += data +\
              self.stream.charsUntil((u"'", u"&"))
        return True
    attributeValueSingleQuotedState.func_annotations = {}

    def attributeValueUnQuotedState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == u"&":
            self.processEntityInAttribute(u">")
        elif data == u">":
            self.emitCurrentToken()
        elif data in (u'"', u"'", u"=", u"<", u"`"):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-character-in-unquoted-attribute-value"})
            self.currentToken[u"data"][-1][1] += data
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"][-1][1] += u"\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-attribute-value-no-quotes"})
            self.state = self.dataState
        else:
            self.currentToken[u"data"][-1][1] += data + self.stream.charsUntil(
              frozenset((u"&", u">", u'"', u"'", u"=", u"<", u"`")) | spaceCharacters)
        return True
    attributeValueUnQuotedState.func_annotations = {}

    def afterAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"/":
            self.state = self.selfClosingStartTagState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-EOF-after-attribute-value"})
            self.stream.unget(data)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-character-after-attribute-value"})
            self.stream.unget(data)
            self.state = self.beforeAttributeNameState
        return True
    afterAttributeValueState.func_annotations = {}

    def selfClosingStartTagState(self):
        data = self.stream.char()
        if data == u">":
            self.currentToken[u"selfClosing"] = True
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data":
                                        u"unexpected-EOF-after-solidus-in-tag"})
            self.stream.unget(data)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-character-after-soldius-in-tag"})
            self.stream.unget(data)
            self.state = self.beforeAttributeNameState
        return True
    selfClosingStartTagState.func_annotations = {}

    def bogusCommentState(self):
        # Make a new comment token and give it as value all the characters
        # until the first > or EOF (charsUntil checks for EOF automatically)
        # and emit it.
        data = self.stream.charsUntil(u">")
        data = data.replace(u"\u0000", u"\uFFFD")
        self.tokenQueue.append(
          {u"type": tokenTypes[u"Comment"], u"data": data})

        # Eat the character directly after the bogus comment which is either a
        # ">" or an EOF.
        self.stream.char()
        self.state = self.dataState
        return True
    bogusCommentState.func_annotations = {}

    def markupDeclarationOpenState(self):
        charStack = [self.stream.char()]
        if charStack[-1] == u"-":
            charStack.append(self.stream.char())
            if charStack[-1] == u"-":
                self.currentToken = {u"type": tokenTypes[u"Comment"], u"data": u""}
                self.state = self.commentStartState
                return True
        elif charStack[-1] in (u'd', u'D'):
            matched = True
            for expected in ((u'o', u'O'), (u'c', u'C'), (u't', u'T'),
                             (u'y', u'Y'), (u'p', u'P'), (u'e', u'E')):
                charStack.append(self.stream.char())
                if charStack[-1] not in expected:
                    matched = False
                    break
            if matched:
                self.currentToken = {u"type": tokenTypes[u"Doctype"],
                                     u"name": u"",
                                     u"publicId": None, u"systemId": None, 
                                     u"correct": True}
                self.state = self.doctypeState
                return True
        elif (charStack[-1] == u"[" and 
              self.parser is not None and
              self.parser.tree.openElements and
              self.parser.tree.openElements[-1].namespace != self.parser.tree.defaultNamespace):
            matched = True
            for expected in [u"C", u"D", u"A", u"T", u"A", u"["]:
                charStack.append(self.stream.char())
                if charStack[-1] != expected:
                    matched = False
                    break
            if matched:
                self.state = self.cdataSectionState
                return True

        self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
          u"expected-dashes-or-doctype"})

        while charStack:
            self.stream.unget(charStack.pop())
        self.state = self.bogusCommentState
        return True
    markupDeclarationOpenState.func_annotations = {}

    def commentStartState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.commentStartDashState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"incorrect-comment"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"data"] += data
            self.state = self.commentState
        return True
    commentStartState.func_annotations = {}
    
    def commentStartDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.commentEndState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"-\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"incorrect-comment"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"data"] += u"-" + data
            self.state = self.commentState
        return True
    commentStartDashState.func_annotations = {}

    
    def commentState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.commentEndDashState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"data"] += data + \
                self.stream.charsUntil((u"-", u"\u0000"))
        return True
    commentState.func_annotations = {}

    def commentEndDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.commentEndState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"-\uFFFD"
            self.state = self.commentState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-comment-end-dash"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"data"] += u"-" + data
            self.state = self.commentState
        return True
    commentEndDashState.func_annotations = {}

    def commentEndState(self):
        data = self.stream.char()
        if data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"--\uFFFD"
            self.state = self.commentState
        elif data == u"!":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-bang-after-double-dash-in-comment"})
            self.state = self.commentEndBangState
        elif data == u"-":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
             u"unexpected-dash-after-double-dash-in-comment"})
            self.currentToken[u"data"] += data
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-comment-double-dash"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            # XXX
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-comment"})
            self.currentToken[u"data"] += u"--" + data
            self.state = self.commentState
        return True
    commentEndState.func_annotations = {}

    def commentEndBangState(self):
        data = self.stream.char()
        if data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u"-":
            self.currentToken[u"data"] += u"--!"
            self.state = self.commentEndDashState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"data"] += u"--!\uFFFD"
            self.state = self.commentState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-comment-end-bang-state"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"data"] += u"--!" + data
            self.state = self.commentState
        return True
    commentEndBangState.func_annotations = {}

    def doctypeState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypeNameState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-doctype-name-but-got-eof"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"need-space-after-doctype"})
            self.stream.unget(data)
            self.state = self.beforeDoctypeNameState
        return True
    doctypeState.func_annotations = {}

    def beforeDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-doctype-name-but-got-right-bracket"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"name"] = u"\uFFFD"
            self.state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"expected-doctype-name-but-got-eof"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"name"] = data
            self.state = self.doctypeNameState
        return True
    beforeDoctypeNameState.func_annotations = {}

    def doctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.currentToken[u"name"] = self.currentToken[u"name"].translate(asciiUpper2Lower)
            self.state = self.afterDoctypeNameState
        elif data == u">":
            self.currentToken[u"name"] = self.currentToken[u"name"].translate(asciiUpper2Lower)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"name"] += u"\uFFFD"
            self.state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype-name"})
            self.currentToken[u"correct"] = False
            self.currentToken[u"name"] = self.currentToken[u"name"].translate(asciiUpper2Lower)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"name"] += data
        return True
    doctypeNameState.func_annotations = {}

    def afterDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.currentToken[u"correct"] = False
            self.stream.unget(data)
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            if data in (u"p", u"P"):
                matched = True
                for expected in ((u"u", u"U"), (u"b", u"B"), (u"l", u"L"),
                                 (u"i", u"I"), (u"c", u"C")):
                    data = self.stream.char()
                    if data not in expected:
                        matched = False
                        break
                if matched:
                    self.state = self.afterDoctypePublicKeywordState
                    return True
            elif data in (u"s", u"S"):
                matched = True
                for expected in ((u"y", u"Y"), (u"s", u"S"), (u"t", u"T"),
                                 (u"e", u"E"), (u"m", u"M")):
                    data = self.stream.char()
                    if data not in expected:
                        matched = False
                        break
                if matched:
                    self.state = self.afterDoctypeSystemKeywordState
                    return True

            # All the characters read before the current 'data' will be
            # [a-zA-Z], so they're garbage in the bogus doctype and can be
            # discarded; only the latest character might be '>' or EOF
            # and needs to be ungetted
            self.stream.unget(data)
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
                u"expected-space-or-right-bracket-in-doctype", u"datavars":
                {u"data": data}})
            self.currentToken[u"correct"] = False
            self.state = self.bogusDoctypeState

        return True
    afterDoctypeNameState.func_annotations = {}
    
    def afterDoctypePublicKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypePublicIdentifierState
        elif data in (u"'", u'"'):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.stream.unget(data)
            self.state = self.beforeDoctypePublicIdentifierState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.stream.unget(data)
            self.state = self.beforeDoctypePublicIdentifierState
        return True
    afterDoctypePublicKeywordState.func_annotations = {}

    def beforeDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u"\"":
            self.currentToken[u"publicId"] = u""
            self.state = self.doctypePublicIdentifierDoubleQuotedState
        elif data == u"'":
            self.currentToken[u"publicId"] = u""
            self.state = self.doctypePublicIdentifierSingleQuotedState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-end-of-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"correct"] = False
            self.state = self.bogusDoctypeState
        return True
    beforeDoctypePublicIdentifierState.func_annotations = {}

    def doctypePublicIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == u"\"":
            self.state = self.afterDoctypePublicIdentifierState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"publicId"] += u"\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-end-of-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"publicId"] += data
        return True
    doctypePublicIdentifierDoubleQuotedState.func_annotations = {}

    def doctypePublicIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == u"'":
            self.state = self.afterDoctypePublicIdentifierState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"publicId"] += u"\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-end-of-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"publicId"] += data
        return True
    doctypePublicIdentifierSingleQuotedState.func_annotations = {}

    def afterDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.betweenDoctypePublicAndSystemIdentifiersState
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u'"':
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == u"'":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"correct"] = False
            self.state = self.bogusDoctypeState
        return True
    afterDoctypePublicIdentifierState.func_annotations = {}
    
    def betweenDoctypePublicAndSystemIdentifiersState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == u'"':
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == u"'":
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"correct"] = False
            self.state = self.bogusDoctypeState
        return True
    betweenDoctypePublicAndSystemIdentifiersState.func_annotations = {}
    
    def afterDoctypeSystemKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypeSystemIdentifierState
        elif data in (u"'", u'"'):
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.stream.unget(data)
            self.state = self.beforeDoctypeSystemIdentifierState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.stream.unget(data)
            self.state = self.beforeDoctypeSystemIdentifierState
        return True
    afterDoctypeSystemKeywordState.func_annotations = {}
    
    def beforeDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u"\"":
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == u"'":
            self.currentToken[u"systemId"] = u""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.currentToken[u"correct"] = False
            self.state = self.bogusDoctypeState
        return True
    beforeDoctypeSystemIdentifierState.func_annotations = {}

    def doctypeSystemIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == u"\"":
            self.state = self.afterDoctypeSystemIdentifierState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"systemId"] += u"\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-end-of-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"systemId"] += data
        return True
    doctypeSystemIdentifierDoubleQuotedState.func_annotations = {}

    def doctypeSystemIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == u"'":
            self.state = self.afterDoctypeSystemIdentifierState
        elif data == u"\u0000":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                    u"data": u"invalid-codepoint"})
            self.currentToken[u"systemId"] += u"\uFFFD"
        elif data == u">":
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-end-of-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken[u"systemId"] += data
        return True
    doctypeSystemIdentifierSingleQuotedState.func_annotations = {}

    def afterDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"eof-in-doctype"})
            self.currentToken[u"correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], u"data":
              u"unexpected-char-in-doctype"})
            self.state = self.bogusDoctypeState
        return True
    afterDoctypeSystemIdentifierState.func_annotations = {}

    def bogusDoctypeState(self):
        data = self.stream.char()
        if data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            # XXX EMIT
            self.stream.unget(data)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            pass
        return True
    bogusDoctypeState.func_annotations = {}

    def cdataSectionState(self):
        data = []
        while True:
            data.append(self.stream.charsUntil(u"]"))
            data.append(self.stream.charsUntil(u">"))
            char = self.stream.char()
            if char == EOF:
                break
            else:
                assert char == u">"
                if data[-1][-2:] == u"]]":
                    data[-1] = data[-1][:-2]
                    break
                else:
                    data.append(char)

        data = u"".join(data)
        #Deal with null here rather than in the parser
        nullCount = data.count(u"\u0000")
        if nullCount > 0:
            for i in xrange(nullCount):
                self.tokenQueue.append({u"type": tokenTypes[u"ParseError"], 
                                        u"data": u"invalid-codepoint"})
            data = data.replace(u"\u0000", u"\uFFFD")
        if data:
            self.tokenQueue.append({u"type": tokenTypes[u"Characters"], 
                                    u"data": data})
        self.state = self.dataState
        return True
    cdataSectionState.func_annotations = {}
