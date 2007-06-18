try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset
import gettext
_ = gettext.gettext

from constants import contentModelFlags, spaceCharacters
from constants import entitiesWindows1252, entities
from constants import asciiLowercase, asciiLetters, asciiUpper2Lower
from constants import digits, hexDigits, EOF

from inputstream import HTMLInputStream

class HTMLTokenizer(object):
    """ This class takes care of tokenizing HTML.

    * self.currentToken
      Holds the token that is currently being processed.

    * self.state
      Holds a reference to the method to be invoked... XXX

    * self.states
      Holds a mapping between states and methods that implement the state.

    * self.stream
      Points to HTMLInputStream object.
    """

    # XXX need to fix documentation

    def __init__(self, stream, encoding=None, parseMeta=True):
        self.stream = HTMLInputStream(stream, encoding, parseMeta)

        self.states = {
            "data":self.dataState,
            "entityData":self.entityDataState,
            "tagOpen":self.tagOpenState,
            "closeTagOpen":self.closeTagOpenState,
            "tagName":self.tagNameState,
            "beforeAttributeName":self.beforeAttributeNameState,
            "attributeName":self.attributeNameState,
            "afterAttributeName":self.afterAttributeNameState,
            "beforeAttributeValue":self.beforeAttributeValueState,
            "attributeValueDoubleQuoted":self.attributeValueDoubleQuotedState,
            "attributeValueSingleQuoted":self.attributeValueSingleQuotedState,
            "attributeValueUnQuoted":self.attributeValueUnQuotedState,
            "bogusComment":self.bogusCommentState,
            "markupDeclarationOpen":self.markupDeclarationOpenState,
            "comment":self.commentState,
            "commentDash":self.commentDashState,
            "commentEnd":self.commentEndState,
            "doctype":self.doctypeState,
            "beforeDoctypeName":self.beforeDoctypeNameState,
            "doctypeName":self.doctypeNameState,
            "afterDoctypeName":self.afterDoctypeNameState,
            "beforeDoctypePublicIdentifier":self.beforeDoctypePublicIdentifierState,
            "doctypePublicIdentifierDoubleQuoted":self.doctypePublicIdentifierDoubleQuotedState,
            "doctypePublicIdentifierSingleQuoted":self.doctypePublicIdentifierSingleQuotedState,
            "afterDoctypePublicIdentifier":self.afterDoctypePublicIdentifierState,
            "beforeDoctypeSystemIdentifier":self.beforeDoctypeSystemIdentifierState,
            "doctypeSystemIdentifierDoubleQuoted":self.doctypeSystemIdentifierDoubleQuotedState,
            "doctypeSystemIdentifierSingleQuoted":self.doctypeSystemIdentifierSingleQuotedState,
            "afterDoctypeSystemIdentifier":self.afterDoctypeSystemIdentifierState,
            "bogusDoctype":self.bogusDoctypeState
        }

        # Setup the initial tokenizer state
        self.contentModelFlag = contentModelFlags["PCDATA"]
        self.state = self.states["data"]

        # The current token being created
        self.currentToken = None

        # Tokens to be processed.
        self.tokenQueue = []

    def __iter__(self):
        """ This is where the magic happens.

        We do our usually processing through the states and when we have a token
        to return we yield the token which pauses processing until the next token
        is requested.
        """
        self.tokenQueue = []
        # Start processing. When EOF is reached self.state will return False
        # instead of True and the loop will terminate.
        while self.state():
            while self.tokenQueue:
                yield self.tokenQueue.pop(0)

    # Below are various helper functions the tokenizer states use worked out.
    def processSolidusInTag(self):
        """If the next character is a '>', convert the currentToken into
        an EmptyTag
        """

        # We need to consume another character to make sure it's a ">"
        data = self.stream.char()

        if self.currentToken["type"] == "StartTag" and data == u">":
            self.currentToken["type"] = "EmptyTag"
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Solidus (/) incorrectly placed in tag.")})

        # The character we just consumed need to be put back on the stack so it
        # doesn't get lost...
        self.stream.queue.append(data)

    def consumeNumberEntity(self, isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.tokenQueue.append({"type": "ParseError"}) is invoked.
        """

        # XXX More need to be done here. For instance, #13 should prolly be
        # converted to #10 so we don't get \r (#13 is \r right?) in the DOM and
        # such. Thoughts on this appreciated.
        allowed = digits
        radix = 10
        if isHex:
            allowed = hexDigits
            radix = 16

        char = u"\uFFFD"
        charStack = []

        # Consume all the characters that are in range while making sure we
        # don't hit an EOF.
        c = self.stream.char()
        while c in allowed and c is not EOF:
            charStack.append(c)
            c = self.stream.char()

        # Convert the set of characters consumed to an int.
        charAsInt = int("".join(charStack), radix)

        # If the integer is between 127 and 160 (so 128 and bigger and 159 and
        # smaller) we need to do the "windows trick".
        if 127 < charAsInt < 160:
            #XXX - removed parse error from windows 1252 entity for now
            #we may want to reenable this later
            #self.tokenQueue.append({"type": "ParseError", "data":
            #  _("Entity used with illegal number (windows-1252 reference).")})

            charAsInt = entitiesWindows1252[charAsInt - 128]

        # 0 is not a good number.
        if charAsInt == 0:
            charAsInt = 65533

        try:
            # XXX We should have a separate function that does "int" to
            # "unicodestring" conversion since this doesn't always work
            # according to hsivonen. Also, unichr has a limitation of 65535
            char = unichr(charAsInt)
        except:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Numeric entity couldn't be converted to character.")})

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        if c != u";":
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Numeric entity didn't end with ';'.")})
            self.stream.queue.append(c)

        return char

    def consumeEntity(self):
        char = None
        charStack = [self.stream.char()]
        if charStack[0] == u"#":
            # We might have a number entity here.
            charStack.extend([self.stream.char(), self.stream.char()])
            if EOF in charStack:
                # If we reach the end of the file put everything up to EOF
                # back in the queue
                charStack = charStack[:charStack.index(EOF)]
                self.stream.queue.extend(charStack)
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Numeric entity expected. Got end of file instead.")})
            else:
                if charStack[1].lower() == u"x" \
                  and charStack[2] in hexDigits:
                    # Hexadecimal entity detected.
                    self.stream.queue.append(charStack[2])
                    char = self.consumeNumberEntity(True)
                elif charStack[1] in digits:
                    # Decimal entity detected.
                    self.stream.queue.extend(charStack[1:])
                    char = self.consumeNumberEntity(False)
                else:
                    # No number entity detected.
                    self.stream.queue.extend(charStack)
                    self.tokenQueue.append({"type": "ParseError", "data":
                      _("Numeric entity expected but none found.")})
        # Break out if we reach the end of the file
        elif charStack[0] == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Entity expected. Got end of file instead.")})
        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".
            #
            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer matches.
            filteredEntityList = [e for e in entities if \
              e.startswith(charStack[0])]

            def entitiesStartingWith(name):
                return [e for e in filteredEntityList if e.startswith(name)]

            while charStack[-1] != EOF and\
              entitiesStartingWith("".join(charStack)):
                charStack.append(self.stream.char())

            # At this point we have a string that starts with some characters
            # that may match an entity
            entityName = None

            # Try to find the longest entity the string will match
            for entityLength in xrange(len(charStack)-1,1,-1):
                possibleEntityName = "".join(charStack[:entityLength])
                if possibleEntityName in entities:
                    entityName = possibleEntityName
                    break

            if entityName is not None:
                char = entities[entityName]

                # Check whether or not the last character returned can be
                # discarded or needs to be put back.
                if not charStack[-1] == ";":
                    self.tokenQueue.append({"type": "ParseError", "data":
                      _("Named entity didn't end with ';'.")})
                    self.stream.queue.extend(charStack[entityLength:])
            else:
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Named entity expected. Got none.")})
                self.stream.queue.extend(charStack)
        return char

    def processEntityInAttribute(self):
        """This method replaces the need for "entityInAttributeValueState".
        """
        entity = self.consumeEntity()
        if entity:
            self.currentToken["data"][-1][1] += entity
        else:
            self.currentToken["data"][-1][1] += u"&"

    def emitCurrentToken(self):
        """This method is a generic handler for emitting the tags. It also sets
        the state to "data" because that's what's needed after a token has been
        emitted.
        """

        # Add token to the queue to be yielded
        self.tokenQueue.append(self.currentToken)
        self.state = self.states["data"]


    # Below are the various tokenizer states worked out.

    # XXX AT Perhaps we should have Hixie run some evaluation on billions of
    # documents to figure out what the order of the various if and elif
    # statements should be.

    def dataState(self):
        data = self.stream.char()
        if data == u"&" and self.contentModelFlag in\
          (contentModelFlags["PCDATA"], contentModelFlags["RCDATA"]):
            self.state = self.states["entityData"]
        elif data == u"<" and self.contentModelFlag !=\
          contentModelFlags["PLAINTEXT"]:
            self.state = self.states["tagOpen"]
        elif data == EOF:
            # Tokenization ends.
            return False
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            # XXX need to check if we don't need a special "spaces" flag on
            # characters.
            self.tokenQueue.append({"type": "SpaceCharacters", "data":
              data + self.stream.charsUntil(spaceCharacters, True)})
        else:
            self.tokenQueue.append({"type": "Characters", "data": 
              data + self.stream.charsUntil((u"&", u"<"))})
        return True

    def entityDataState(self):
        entity = self.consumeEntity()
        if entity:
            self.tokenQueue.append({"type": "Characters", "data": entity})
        else:
            self.tokenQueue.append({"type": "Characters", "data": u"&"})
        self.state = self.states["data"]
        return True

    def tagOpenState(self):
        data = self.stream.char()
        if self.contentModelFlag == contentModelFlags["PCDATA"]:
            if data == u"!":
                self.state = self.states["markupDeclarationOpen"]
            elif data == u"/":
                self.state = self.states["closeTagOpen"]
            elif data in asciiLetters:
                self.currentToken =\
                  {"type": "StartTag", "name": data, "data": []}
                self.state = self.states["tagName"]
            elif data == u">":
                # XXX In theory it could be something besides a tag name. But
                # do we really care?
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected tag name. Got '>' instead.")})
                self.tokenQueue.append({"type": "Characters", "data": u"<>"})
                self.state = self.states["data"]
            elif data == u"?":
                # XXX In theory it could be something besides a tag name. But
                # do we really care?
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected tag name. Got '?' instead (HTML doesn't "
                  "support processing instructions).")})
                self.stream.queue.append(data)
                self.state = self.states["bogusComment"]
            else:
                # XXX
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected tag name. Got something else instead")})
                self.tokenQueue.append({"type": "Characters", "data": u"<"})
                self.stream.queue.append(data)
                self.state = self.states["data"]
        else:
            # We know the content model flag is set to either RCDATA or CDATA
            # now because this state can never be entered with the PLAINTEXT
            # flag.
            if data == u"/":
                self.state = self.states["closeTagOpen"]
            else:
                self.tokenQueue.append({"type": "Characters", "data": u"<"})
                self.stream.queue.insert(0, data)
                self.state = self.states["data"]
        return True

    def closeTagOpenState(self):
        if (self.contentModelFlag in (contentModelFlags["RCDATA"],
            contentModelFlags["CDATA"])):
            if self.currentToken:
                charStack = []

                # So far we know that "</" has been consumed. We now need to know
                # whether the next few characters match the name of last emitted
                # start tag which also happens to be the currentToken. We also need
                # to have the character directly after the characters that could
                # match the start tag name.
                for x in xrange(len(self.currentToken["name"]) + 1):
                    charStack.append(self.stream.char())
                    # Make sure we don't get hit by EOF
                    if charStack[-1] == EOF:
                        break

                # Since this is just for checking. We put the characters back on
                # the stack.
                self.stream.queue.extend(charStack)

            if self.currentToken \
              and self.currentToken["name"].lower() == "".join(charStack[:-1]).lower() \
              and charStack[-1] in (spaceCharacters |
              frozenset((u">", u"/", u"<", EOF))):
                # Because the characters are correct we can safely switch to
                # PCDATA mode now. This also means we don't have to do it when
                # emitting the end tag token.
                self.contentModelFlag = contentModelFlags["PCDATA"]
            else:
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected closing tag after seeing '</'. None found.")})
                self.tokenQueue.append({"type": "Characters", "data": u"</"})
                self.state = self.states["data"]

                # Need to return here since we don't want the rest of the
                # method to be walked through.
                return True

        if self.contentModelFlag == contentModelFlags["PCDATA"]:
            data = self.stream.char()
            if data in asciiLetters:
                self.currentToken =\
                  {"type": "EndTag", "name": data, "data": []}
                self.state = self.states["tagName"]
            elif data == u">":
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected closing tag. Got '>' instead. Ignoring '</>'.")})
                self.state = self.states["data"]
            elif data == EOF:
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected closing tag. Unexpected end of file.")})
                self.tokenQueue.append({"type": "Characters", "data": u"</"})
                self.state = self.states["data"]
            else:
                # XXX data can be _'_...
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected closing tag. Unexpected character '" + data + "' found.")})
                self.stream.queue.append(data)
                self.state = self.states["bogusComment"]
        return True

    def tagNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.states["beforeAttributeName"]
        elif data in asciiLetters:
            self.currentToken["name"] += data +\
              self.stream.charsUntil(asciiLetters, True)
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in the tag name.")})
            self.emitCurrentToken()
        elif data == u"/":
            self.processSolidusInTag()
            self.state = self.states["beforeAttributeName"]
        else:
            self.currentToken["name"] += data
        return True

    def beforeAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data in asciiLetters:
            self.currentToken["data"].append([data, ""])
            self.state = self.states["attributeName"]
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"/":
            self.processSolidusInTag()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file. Expected attribute name instead.")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"].append([data, ""])
            self.state = self.states["attributeName"]
        return True

    def attributeNameState(self):
        data = self.stream.char()
        leavingThisState = True
        if data == u"=":
            self.state = self.states["beforeAttributeValue"]
        elif data in asciiLetters:
            self.currentToken["data"][-1][0] += data +\
              self.stream.charsUntil(asciiLetters, True)
            leavingThisState = False
        elif data == u">":
            # XXX If we emit here the attributes are converted to a dict
            # without being checked and when the code below runs we error
            # because data is a dict not a list
            pass
        elif data in spaceCharacters:
            self.state = self.states["afterAttributeName"]
        elif data == u"/":
            self.processSolidusInTag()
            self.state = self.states["beforeAttributeName"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in attribute name.")})
            self.emitCurrentToken()
            leavingThisState = False
        else:
            self.currentToken["data"][-1][0] += data
            leavingThisState = False

        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            for name, value in self.currentToken["data"][:-1]:
                if self.currentToken["data"][-1][0] == name:
                    self.tokenQueue.append({"type": "ParseError", "data":
                      _("Dropped duplicate attribute on tag.")})
            # XXX Fix for above XXX
            if data == u">":
                self.emitCurrentToken()
        return True

    def afterAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == u"=":
            self.state = self.states["beforeAttributeValue"]
        elif data == u">":
            self.emitCurrentToken()
        elif data in asciiLetters:
            self.currentToken["data"].append([data, ""])
            self.state = self.states["attributeName"]
        elif data == u"/":
            self.processSolidusInTag()
            self.state = self.states["beforeAttributeName"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file. Expected = or end of tag.")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"].append([data, ""])
            self.state = self.states["attributeName"]
        return True

    def beforeAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == u"\"":
            self.state = self.states["attributeValueDoubleQuoted"]
        elif data == u"&":
            self.state = self.states["attributeValueUnQuoted"]
            self.stream.queue.append(data);
        elif data == u"'":
            self.state = self.states["attributeValueSingleQuoted"]
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file. Expected attribute value.")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"][-1][1] += data
            self.state = self.states["attributeValueUnQuoted"]
        return True

    def attributeValueDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.states["beforeAttributeName"]
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in attribute value (\").")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"][-1][1] += data +\
              self.stream.charsUntil(("\"", u"&"))
        return True

    def attributeValueSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.states["beforeAttributeName"]
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in attribute value (').")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"][-1][1] += data +\
              self.stream.charsUntil(("'", u"&"))
        return True

    def attributeValueUnQuotedState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.states["beforeAttributeName"]
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in attribute value.")})
            self.emitCurrentToken()
        else:
            self.currentToken["data"][-1][1] += data + self.stream.charsUntil( \
              frozenset(("&", ">","<")) | spaceCharacters)
        return True

    def bogusCommentState(self):
        # Make a new comment token and give it as value all the characters
        # until the first > or EOF (charsUntil checks for EOF automatically)
        # and emit it.
        self.tokenQueue.append(
          {"type": "Comment", "data": self.stream.charsUntil((u">"))})

        # Eat the character directly after the bogus comment which is either a
        # ">" or an EOF.
        self.stream.char()
        self.state = self.states["data"]
        return True

    def markupDeclarationOpenState(self):
        charStack = [self.stream.char(), self.stream.char()]
        if charStack == [u"-", u"-"]:
            self.currentToken = {"type": "Comment", "data": ""}
            self.state = self.states["comment"]
        else:
            for x in xrange(5):
                charStack.append(self.stream.char())
            # Put in explicit EOF check
            if (not EOF in charStack and
                "".join(charStack).upper() == u"DOCTYPE"):
                self.currentToken = {"type":"Doctype", "name":"",
                  "publicId":None, "systemId":None, "correct":True}
                self.state = self.states["doctype"]
            else:
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected '--' or 'DOCTYPE'. Not found.")})
                self.stream.queue.extend(charStack)
                self.state = self.states["bogusComment"]
        return True

    def commentState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.states["commentDash"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in comment.")})
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["data"] += data + self.stream.charsUntil(u"-")
        return True

    def commentDashState(self):
        data = self.stream.char()
        if data == u"-":
            self.state = self.states["commentEnd"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in comment (-)")})
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["data"] += u"-" + data +\
              self.stream.charsUntil(u"-")
            # Consume the next character which is either a "-" or an EOF as
            # well so if there's a "-" directly after the "-" we go nicely to
            # the "comment end state" without emitting a ParseError() there.
            self.stream.char()
        return True

    def commentEndState(self):
        data = self.stream.char()
        if data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == u"-":
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected '-' after '--' found in comment.")})
            self.currentToken["data"] += data
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in comment (--).")})
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            # XXX
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in comment found.")})
            self.currentToken["data"] += u"--" + data
            self.state = self.states["comment"]
        return True

    def doctypeState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.states["beforeDoctypeName"]
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("No space after literal string 'DOCTYPE'.")})
            self.stream.queue.append(data)
            self.state = self.states["beforeDoctypeName"]
        return True

    def beforeDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected > character. Expected DOCTYPE name.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file. Expected DOCTYPE name.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["name"] = data
            self.state = self.states["doctypeName"]
        return True

    def doctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.states["afterDoctypeName"]
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE name.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["name"] += data
        return True

    def afterDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.currentToken["correct"] = False
            self.stream.queue.append(data)
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            charStack = []
            for x in xrange(6):
                charStack.append(self.stream.char())
            if EOF not in charStack and\
              "".join(charStack).translate(asciiUpper2Lower) == "public":
                self.state = self.states["beforeDoctypePublicIdentifier"]
            elif EOF not in charStack and\
              "".join(charStack).translate(asciiUpper2Lower) == "system":
                self.state = self.states["beforeDoctypeSystemIdentifier"]
            else:
                self.stream.queue.extend(charStack)
                self.tokenQueue.append({"type": "ParseError", "data":
                  _("Expected space or '>'. Got '" + data + "'")})
                self.state = self.states["bogusDoctype"]
        return True
    
    def beforeDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken["publicId"] = ""
            self.state = self.states["doctypePublicIdentifierDoubleQuoted"]
        elif data == "'":
            self.currentToken["publicId"] = ""
            self.state = self.states["doctypePublicIdentifierSingleQuoted"]
        elif data == ">":
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in DOCTYPE.")})
            self.state = self.states["bogusDoctype"]
        return True

    def doctypePublicIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.states["afterDoctypePublicIdentifier"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["publicId"] += data
        return True

    def doctypePublicIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.states["afterDoctypePublicIdentifier"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["publicId"] += data
        return True

    def afterDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken["systemId"] = ""
            self.state = self.states["doctypeSystemIdentifierDoubleQuoted"]
        elif data == "'":
            self.currentToken["systemId"] = ""
            self.state = self.states["doctypeSystemIdentifierSinglequoted"]
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in DOCTYPE.")})
            self.state = self.states["bogusDoctype"]
        return True
    
    def beforeDoctypeSystemIdentifierState(self):
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken["systemId"] = ""
            self.state = self.states["doctypeSystemIdentifierDoubleQuoted"]
        elif data == "'":
            self.currentToken["systemId"] = ""
            self.state = self.states["doctypeSystemIdentifierSinglequoted"]
        elif data == ">":
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in DOCTYPE.")})
            self.state = self.states["bogusDoctype"]
        return True

    def doctypeSystemIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.states["afterDoctypeSystemIdentifier"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["systemId"] += data
        return True

    def doctypeSystemIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.states["afterDoctypeSystemIdentifier"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.currentToken["systemId"] += data
        return True

    def afterDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in DOCTYPE.")})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected character in DOCTYPE.")})
            self.state = self.states["bogusDoctype"]
        return True

    def bogusDoctypeState(self):
        data = self.stream.char()
        self.currentToken["correct"] = False
        if data == u">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        elif data == EOF:
            # XXX EMIT
            self.stream.queue.append(data)
            self.tokenQueue.append({"type": "ParseError", "data":
              _("Unexpected end of file in bogus doctype.")})
            self.tokenQueue.append(self.currentToken)
            self.state = self.states["data"]
        else:
            pass
        return True
