from __future__ import absolute_import
import codecs
import re
import types
import sys

from .constants import EOF, spaceCharacters, asciiLetters, asciiUppercase
from .constants import encodings, ReparseException
from . import utils

from io import StringIO

try:
    from io import BytesIO
except ImportError:
    BytesIO = StringIO

try:
    from io import BufferedIOBase
except ImportError:
    class BufferedIOBase(object):
        pass

#Non-unicode versions of constants for use in the pre-parser
spaceCharactersBytes = frozenset([item.encode(u"ascii") for item in spaceCharacters])
asciiLettersBytes = frozenset([item.encode(u"ascii") for item in asciiLetters])
asciiUppercaseBytes = frozenset([item.encode(u"ascii") for item in asciiUppercase])
spacesAngleBrackets = spaceCharactersBytes | frozenset([">", "<"])

invalid_unicode_re = re.compile(u"[\u0001-\u0008\u000B\u000E-\u001F\u007F-\u009F\uD800-\uDFFF\uFDD0-\uFDEF\uFFFE\uFFFF\U0001FFFE\U0001FFFF\U0002FFFE\U0002FFFF\U0003FFFE\U0003FFFF\U0004FFFE\U0004FFFF\U0005FFFE\U0005FFFF\U0006FFFE\U0006FFFF\U0007FFFE\U0007FFFF\U0008FFFE\U0008FFFF\U0009FFFE\U0009FFFF\U000AFFFE\U000AFFFF\U000BFFFE\U000BFFFF\U000CFFFE\U000CFFFF\U000DFFFE\U000DFFFF\U000EFFFE\U000EFFFF\U000FFFFE\U000FFFFF\U0010FFFE\U0010FFFF]")

non_bmp_invalid_codepoints = set([0x1FFFE, 0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE,
                                  0x3FFFF, 0x4FFFE, 0x4FFFF, 0x5FFFE, 0x5FFFF,
                                  0x6FFFE, 0x6FFFF, 0x7FFFE, 0x7FFFF, 0x8FFFE,
                                  0x8FFFF, 0x9FFFE, 0x9FFFF, 0xAFFFE, 0xAFFFF,
                                  0xBFFFE, 0xBFFFF, 0xCFFFE, 0xCFFFF, 0xDFFFE,
                                  0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE, 0xFFFFF,
                                  0x10FFFE, 0x10FFFF])

ascii_punctuation_re = re.compile(u"[\u0009-\u000D\u0020-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]")

# Cache for charsUntil()
charsUntilRegEx = {}
        
class BufferedStream(object):
    u"""Buffering for streams that do not have buffering of their own

    The buffer is implemented as a list of chunks on the assumption that 
    joining many strings will be slow since it is O(n**2)
    """
    
    def __init__(self, stream):
        self.stream = stream
        self.buffer = []
        self.position = [-1,0] #chunk number, offset
    __init__.func_annotations = {}

    def tell(self):
        pos = 0
        for chunk in self.buffer[:self.position[0]]:
            pos += len(chunk)
        pos += self.position[1]
        return pos
    tell.func_annotations = {}

    def seek(self, pos):
        assert pos < self._bufferedBytes()
        offset = pos
        i = 0
        while len(self.buffer[i]) < offset:
            offset -= pos
            i += 1
        self.position = [i, offset]
    seek.func_annotations = {}

    def read(self, str):
        if not self.buffer:
            return self._readStream(str)
        elif (self.position[0] == len(self.buffer) and
              self.position[1] == len(self.buffer[-1])):
            return self._readStream(str)
        else:
            return self._readFromBuffer(str)
    read.func_annotations = {}
    
    def _bufferedBytes(self):
        return sum([len(item) for item in self.buffer])
    _bufferedBytes.func_annotations = {}

    def _readStream(self, str):
        data = self.stream.read(str)
        self.buffer.append(data)
        self.position[0] += 1
        self.position[1] = len(data)
        return data
    _readStream.func_annotations = {}

    def _readFromBuffer(self, str):
        remainingBytes = str
        rv = []
        bufferIndex = self.position[0]
        bufferOffset = self.position[1]
        while bufferIndex < len(self.buffer) and remainingBytes != 0:
            assert remainingBytes > 0
            bufferedData = self.buffer[bufferIndex]
            
            if remainingBytes <= len(bufferedData) - bufferOffset:
                bytesToRead = remainingBytes
                self.position = [bufferIndex, bufferOffset + bytesToRead]
            else:
                bytesToRead = len(bufferedData) - bufferOffset
                self.position = [bufferIndex, len(bufferedData)]
                bufferIndex += 1
            data = rv.append(bufferedData[bufferOffset: 
                                          bufferOffset + bytesToRead])
            remainingBytes -= bytesToRead

            bufferOffset = 0

        if remainingBytes:
            rv.append(self._readStream(remainingBytes))
        
        return u"".join(rv)
    _readFromBuffer.func_annotations = {}


def HTMLInputStream(source, encoding=None, parseMeta=True, chardet=True):
    if hasattr(source, u"read"):
        isUnicode = isinstance(source.read(0), unicode)
    else:
        isUnicode = isinstance(source, unicode)

    if isUnicode:
        if encoding is not None:
            raise TypeError(u"Cannot explicitly set an encoding with a unicode string")
        return HTMLUnicodeInputStream(source)
    else:
        return HTMLBinaryInputStream(source, encoding, parseMeta, chardet)
HTMLInputStream.func_annotations = {}


class HTMLUnicodeInputStream(object):
    u"""Provides a unicode stream of characters to the HTMLTokenizer.

    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.

    """

    _defaultChunkSize = 10240

    def __init__(self, source):
        u"""Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by html5lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        
        parseMeta - Look for a <meta> element containing encoding information

        """

        #Craziness
        if len(u"\U0010FFFF") == 1:
            self.reportCharacterErrors = self.characterErrorsUCS4
            self.replaceCharactersRegexp = re.compile(u"[\uD800-\uDFFF]")
        else:
            self.reportCharacterErrors = self.characterErrorsUCS2
            self.replaceCharactersRegexp = re.compile(u"([\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF])")

        # List of where new lines occur
        self.newLines = [0]

        self.charEncoding = (u"utf-8", u"certain")
        self.dataStream = self.openStream(source)

        self.reset()
    __init__.func_annotations = {}

    def reset(self):
        self.chunk = u""
        self.chunkSize = 0
        self.chunkOffset = 0
        self.errors = []

        # number of (complete) lines in previous chunks
        self.prevNumLines = 0
        # number of columns in the last line of the previous chunk
        self.prevNumCols = 0
        
        #Deal with CR LF and surrogates split over chunk boundaries
        self._bufferedCharacter = None
    reset.func_annotations = {}

    def openStream(self, source):
        u"""Produces a file object from source.

        source can be either a file object, local filename or a string.

        """
        # Already a file object
        if hasattr(source, u'read'):
            stream = source
        else:
            stream = StringIO(source)

        if (#not isinstance(stream, BufferedIOBase) and
            not(hasattr(stream, u"tell") and
                hasattr(stream, u"seek")) or
            stream is sys.stdin):
            stream = BufferedStream(stream)

        return stream
    openStream.func_annotations = {}

    def _position(self, offset):
        chunk = self.chunk
        nLines = chunk.count(u'\n', 0, offset)
        positionLine = self.prevNumLines + nLines
        lastLinePos = chunk.rfind(u'\n', 0, offset)
        if lastLinePos == -1:
            positionColumn = self.prevNumCols + offset
        else:
            positionColumn = offset - (lastLinePos + 1)
        return (positionLine, positionColumn)
    _position.func_annotations = {}

    def position(self):
        u"""Returns (line, col) of the current position in the stream."""
        line, col = self._position(self.chunkOffset)
        return (line+1, col)
    position.func_annotations = {}

    def char(self):
        u""" Read one character from the stream or queue if available. Return
            EOF when EOF is reached.
        """
        # Read a new chunk from the input stream if necessary
        if self.chunkOffset >= self.chunkSize:
            if not self.readChunk():
                return EOF

        chunkOffset = self.chunkOffset
        char = self.chunk[chunkOffset]
        self.chunkOffset = chunkOffset + 1

        return char
    char.func_annotations = {}

    def readChunk(self, chunkSize=None):
        if chunkSize is None:
            chunkSize = self._defaultChunkSize

        self.prevNumLines, self.prevNumCols = self._position(self.chunkSize)

        self.chunk = u""
        self.chunkSize = 0
        self.chunkOffset = 0

        data = self.dataStream.read(chunkSize)
        
        #Deal with CR LF and surrogates broken across chunks
        if self._bufferedCharacter:
            data = self._bufferedCharacter + data
            self._bufferedCharacter = None
        elif not data:
            # We have no more data, bye-bye stream
            return False
        
        if len(data) > 1:
            lastv = ord(data[-1])
            if lastv == 0x0D or 0xD800 <= lastv <= 0xDBFF:
                self._bufferedCharacter = data[-1]
                data = data[:-1]
        
        self.reportCharacterErrors(data)
        
        # Replace invalid characters
        # Note U+0000 is dealt with in the tokenizer
        data = self.replaceCharactersRegexp.sub(u"\ufffd", data)
                    
        data = data.replace(u"\r\n", u"\n")
        data = data.replace(u"\r", u"\n")

        self.chunk = data
        self.chunkSize = len(data)

        return True
    readChunk.func_annotations = {}

    def characterErrorsUCS4(self, data):
        for i in xrange(len(invalid_unicode_re.findall(data))):
            self.errors.append(u"invalid-codepoint")
    characterErrorsUCS4.func_annotations = {}

    def characterErrorsUCS2(self, data):
        #Someone picked the wrong compile option
        #You lose
        skip = False
        import sys
        for match in invalid_unicode_re.finditer(data):
            if skip:
                continue
            codepoint = ord(match.group())
            pos = match.start()
            #Pretty sure there should be endianness issues here
            if utils.isSurrogatePair(data[pos:pos+2]):
                #We have a surrogate pair!
                char_val = utils.surrogatePairToCodepoint(data[pos:pos+2])
                if char_val in non_bmp_invalid_codepoints:
                    self.errors.append(u"invalid-codepoint")
                skip = True
            elif (codepoint >= 0xD800 and codepoint <= 0xDFFF and
                  pos == len(data) - 1):
                self.errors.append(u"invalid-codepoint")
            else:
                skip = False
                self.errors.append(u"invalid-codepoint")
    characterErrorsUCS2.func_annotations = {}

    def charsUntil(self, characters, opposite = False):
        u""" Returns a string of characters from the stream up to but not
        including any character in 'characters' or EOF. 'characters' must be
        a container that supports the 'in' method and iteration over its
        characters.
        """

        # Use a cache of regexps to find the required characters
        try:
            chars = charsUntilRegEx[(characters, opposite)]
        except KeyError:
            if __debug__:
                for c in characters: 
                    assert(ord(c) < 128)
            regex = u"".join([u"\\x%02x" % ord(c) for c in characters])
            if not opposite:
                regex = u"^%s" % regex
            chars = charsUntilRegEx[(characters, opposite)] = re.compile(u"[%s]+" % regex)

        rv = []

        while True:
            # Find the longest matching prefix
            m = chars.match(self.chunk, self.chunkOffset)
            if m is None:
                # If nothing matched, and it wasn't because we ran out of chunk,
                # then stop
                if self.chunkOffset != self.chunkSize:
                    break
            else:
                end = m.end()
                # If not the whole chunk matched, return everything
                # up to the part that didn't match
                if end != self.chunkSize:
                    rv.append(self.chunk[self.chunkOffset:end])
                    self.chunkOffset = end
                    break
            # If the whole remainder of the chunk matched,
            # use it all and read the next chunk
            rv.append(self.chunk[self.chunkOffset:])
            if not self.readChunk():
                # Reached EOF
                break

        r = u"".join(rv)
        return r
    charsUntil.func_annotations = {}

    def unget(self, char):
        # Only one character is allowed to be ungotten at once - it must
        # be consumed again before any further call to unget
        if char is not None:
            if self.chunkOffset == 0:
                # unget is called quite rarely, so it's a good idea to do
                # more work here if it saves a bit of work in the frequently
                # called char and charsUntil.
                # So, just prepend the ungotten character onto the current
                # chunk:
                self.chunk = char + self.chunk
                self.chunkSize += 1
            else:
                self.chunkOffset -= 1
                assert self.chunk[self.chunkOffset] == char
    unget.func_annotations = {}

class HTMLBinaryInputStream(HTMLUnicodeInputStream):
    u"""Provides a unicode stream of characters to the HTMLTokenizer.

    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.

    """

    def __init__(self, source, encoding=None, parseMeta=True, chardet=True):
        u"""Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by html5lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        
        parseMeta - Look for a <meta> element containing encoding information

        """
        # Raw Stream - for unicode objects this will encode to utf-8 and set
        #              self.charEncoding as appropriate
        self.rawStream = self.openStream(source)

        HTMLUnicodeInputStream.__init__(self, self.rawStream)

        self.charEncoding = (codecName(encoding), u"certain")

        # Encoding Information
        #Number of bytes to use when looking for a meta element with
        #encoding information
        self.numBytesMeta = 512
        #Number of bytes to use when using detecting encoding using chardet
        self.numBytesChardet = 100
        #Encoding to use if no other information can be found
        self.defaultEncoding = u"windows-1252"
        
        #Detect encoding iff no explicit "transport level" encoding is supplied
        if (self.charEncoding[0] is None):
            self.charEncoding = self.detectEncoding(parseMeta, chardet)

        #Call superclass
        self.reset()
    __init__.func_annotations = {}

    def reset(self):
        self.dataStream = codecs.getreader(self.charEncoding[0])(self.rawStream,
                                                                 u'replace')
        HTMLUnicodeInputStream.reset(self)
    reset.func_annotations = {}

    def openStream(self, source):
        u"""Produces a file object from source.

        source can be either a file object, local filename or a string.

        """
        # Already a file object
        if hasattr(source, u'read'):
            stream = source
        else:
            stream = BytesIO(source)

        if (not(hasattr(stream, u"tell") and hasattr(stream, u"seek")) or
            stream is sys.stdin):
            stream = BufferedStream(stream)

        return stream
    openStream.func_annotations = {}

    def detectEncoding(self, parseMeta=True, chardet=True):
        #First look for a BOM
        #This will also read past the BOM if present
        encoding = self.detectBOM()
        confidence = u"certain"
        #If there is no BOM need to look for meta elements with encoding 
        #information
        if encoding is None and parseMeta:
            encoding = self.detectEncodingMeta()
            confidence = u"tentative"
        #Guess with chardet, if avaliable
        if encoding is None and chardet:
            confidence = u"tentative"
            try:
                from chardet.universaldetector import UniversalDetector
                buffers = []
                detector = UniversalDetector()
                while not detector.done:
                    buffer = self.rawStream.read(self.numBytesChardet)
                    assert isinstance(buffer, str)
                    if not buffer:
                        break
                    buffers.append(buffer)
                    detector.feed(buffer)
                detector.close()
                encoding = detector.result[u'encoding']
                self.rawStream.seek(0)
            except ImportError:
                pass
        # If all else fails use the default encoding
        if encoding is None:
            confidence=u"tentative"
            encoding = self.defaultEncoding
        
        #Substitute for equivalent encodings:
        encodingSub = {u"iso-8859-1":u"windows-1252"}

        if encoding.lower() in encodingSub:
            encoding = encodingSub[encoding.lower()]

        return encoding, confidence
    detectEncoding.func_annotations = {}

    def changeEncoding(self, newEncoding):
        assert self.charEncoding[1] != u"certain"
        newEncoding = codecName(newEncoding)
        if newEncoding in (u"utf-16", u"utf-16-be", u"utf-16-le"):
            newEncoding = u"utf-8"
        if newEncoding is None:
            return
        elif newEncoding == self.charEncoding[0]:
            self.charEncoding = (self.charEncoding[0], u"certain")
        else:
            self.rawStream.seek(0)
            self.reset()
            self.charEncoding = (newEncoding, u"certain")
            raise ReparseException(u"Encoding changed from %s to %s"%(self.charEncoding[0], newEncoding))
    changeEncoding.func_annotations = {}
            
    def detectBOM(self):
        u"""Attempts to detect at BOM at the start of the stream. If
        an encoding can be determined from the BOM return the name of the
        encoding otherwise return None"""
        bomDict = {
            codecs.BOM_UTF8: u'utf-8',
            codecs.BOM_UTF16_LE: u'utf-16-le', codecs.BOM_UTF16_BE: u'utf-16-be',
            codecs.BOM_UTF32_LE: u'utf-32-le', codecs.BOM_UTF32_BE: u'utf-32-be'
        }

        # Go to beginning of file and read in 4 bytes
        string = self.rawStream.read(4)
        assert isinstance(string, str)

        # Try detecting the BOM using bytes from the string
        encoding = bomDict.get(string[:3])         # UTF-8
        seek = 3
        if not encoding:
            # Need to detect UTF-32 before UTF-16
            encoding = bomDict.get(string)         # UTF-32
            seek = 4
            if not encoding:
                encoding = bomDict.get(string[:2]) # UTF-16
                seek = 2

        # Set the read position past the BOM if one was found, otherwise
        # set it to the start of the stream
        self.rawStream.seek(encoding and seek or 0)

        return encoding
    detectBOM.func_annotations = {}

    def detectEncodingMeta(self):
        u"""Report the encoding declared by the meta element
        """
        buffer = self.rawStream.read(self.numBytesMeta)
        assert isinstance(buffer, str)
        parser = EncodingParser(buffer)
        self.rawStream.seek(0)
        encoding = parser.getEncoding()
        
        if encoding in (u"utf-16", u"utf-16-be", u"utf-16-le"):
            encoding = u"utf-8"

        return encoding
    detectEncodingMeta.func_annotations = {}

class EncodingBytes(str):
    u"""String-like object with an associated position and various extra methods
    If the position is ever greater than the string length then an exception is
    raised"""
    def __new__(self, value):
        assert isinstance(value, str)
        return str.__new__(self, value.lower())
    __new__.func_annotations = {}

    def __init__(self, value):
        self._position=-1
    __init__.func_annotations = {}
    
    def __iter__(self):
        return self
    __iter__.func_annotations = {}
    
    def next(self):
        p = self._position = self._position + 1
        if p >= len(self):
            raise StopIteration
        elif p < 0:
            raise TypeError
        return self[p:p+1]
    next.func_annotations = {}

    def previous(self):
        p = self._position
        if p >= len(self):
            raise StopIteration
        elif p < 0:
            raise TypeError
        self._position = p = p - 1
        return self[p:p+1]
    previous.func_annotations = {}
    
    def setPosition(self, position):
        if self._position >= len(self):
            raise StopIteration
        self._position = position
    setPosition.func_annotations = {}
    
    def getPosition(self):
        if self._position >= len(self):
            raise StopIteration
        if self._position >= 0:
            return self._position
        else:
            return None
    getPosition.func_annotations = {}
    
    position = property(getPosition, setPosition)

    def getCurrentByte(self):
        return self[self.position:self.position+1]
    getCurrentByte.func_annotations = {}
    
    currentByte = property(getCurrentByte)

    def skip(self, chars=spaceCharactersBytes):
        u"""Skip past a list of characters"""
        p = self.position               # use property for the error-checking
        while p < len(self):
            c = self[p:p+1]
            if c not in chars:
                self._position = p
                return c
            p += 1
        self._position = p
        return None
    skip.func_annotations = {}

    def skipUntil(self, chars):
        p = self.position
        while p < len(self):
            c = self[p:p+1]
            if c in chars:
                self._position = p
                return c
            p += 1
        self._position = p
        return None
    skipUntil.func_annotations = {}

    def matchBytes(self, str):
        u"""Look for a sequence of bytes at the start of a string. If the bytes 
        are found return True and advance the position to the byte after the 
        match. Otherwise return False and leave the position alone"""
        p = self.position
        data = self[p:p+len(str)]
        rv = data.startswith(str)
        if rv:
            self.position += len(str)
        return rv
    matchBytes.func_annotations = {}
    
    def jumpTo(self, str):
        u"""Look for the next sequence of bytes matching a given sequence. If
        a match is found advance the position to the last byte of the match"""
        newPosition = self[self.position:].find(str)
        if newPosition > -1:
            # XXX: This is ugly, but I can't see a nicer way to fix this.
            if self._position == -1:
                self._position = 0
            self._position += (newPosition + len(str)-1)
            return True
        else:
            raise StopIteration
    jumpTo.func_annotations = {}

class EncodingParser(object):
    u"""Mini parser for detecting character encoding from meta elements"""

    def __init__(self, data):
        u"""string - the data to work on for encoding detection"""
        self.data = EncodingBytes(data)
        self.encoding = None
    __init__.func_annotations = {}

    def getEncoding(self):
        methodDispatch = (
            ("<!--",self.handleComment),
            ("<meta",self.handleMeta),
            ("</",self.handlePossibleEndTag),
            ("<!",self.handleOther),
            ("<?",self.handleOther),
            ("<",self.handlePossibleStartTag))
        for byte in self.data:
            keepParsing = True
            for key, method in methodDispatch:
                if self.data.matchBytes(key):
                    try:
                        keepParsing = method()    
                        break
                    except StopIteration:
                        keepParsing=False
                        break
            if not keepParsing:
                break

        return self.encoding
    getEncoding.func_annotations = {}

    def handleComment(self):
        u"""Skip over comments"""
        return self.data.jumpTo("-->")
    handleComment.func_annotations = {}

    def handleMeta(self):
        if self.data.currentByte not in spaceCharactersBytes:
            #if we have <meta not followed by a space so just keep going
            return True
        #We have a valid meta element we want to search for attributes
        hasPragma = False
        pendingEncoding = None
        while True:
            #Try to find the next attribute after the current position
            attr = self.getAttribute()
            if attr is None:
                return True
            else:
                if attr[0] == "http-equiv":
                    hasPragma = attr[1] == "content-type"
                    if hasPragma and pendingEncoding is not None:
                        self.encoding = pendingEncoding
                        return False
                elif attr[0] == "charset":
                    tentativeEncoding = attr[1]
                    codec = codecName(tentativeEncoding)
                    if codec is not None:
                        self.encoding = codec
                        return False
                elif attr[0] == "content":
                    contentParser = ContentAttrParser(EncodingBytes(attr[1]))
                    tentativeEncoding = contentParser.parse()
                    if tentativeEncoding is not None:
                        codec = codecName(tentativeEncoding)
                        if codec is not None:
                            if hasPragma:
                                self.encoding = codec
                                return False
                            else:
                                pendingEncoding = codec
    handleMeta.func_annotations = {}

    def handlePossibleStartTag(self):
        return self.handlePossibleTag(False)
    handlePossibleStartTag.func_annotations = {}

    def handlePossibleEndTag(self):
        self.data.next()
        return self.handlePossibleTag(True)
    handlePossibleEndTag.func_annotations = {}

    def handlePossibleTag(self, endTag):
        data = self.data
        if data.currentByte not in asciiLettersBytes:
            #If the next byte is not an ascii letter either ignore this
            #fragment (possible start tag case) or treat it according to 
            #handleOther
            if endTag:
                data.previous()
                self.handleOther()
            return True
        
        c = data.skipUntil(spacesAngleBrackets)
        if c == "<":
            #return to the first step in the overall "two step" algorithm
            #reprocessing the < byte
            data.previous()
        else:
            #Read all attributes
            attr = self.getAttribute()
            while attr is not None:
                attr = self.getAttribute()
        return True
    handlePossibleTag.func_annotations = {}

    def handleOther(self):
        return self.data.jumpTo(">")
    handleOther.func_annotations = {}

    def getAttribute(self):
        u"""Return a name,value pair for the next attribute in the stream, 
        if one is found, or None"""
        data = self.data
        # Step 1 (skip chars)
        c = data.skip(spaceCharactersBytes | frozenset(["/"]))
        assert c is None or len(c) == 1
        # Step 2
        if c in (">", None):
            return None
        # Step 3
        attrName = []
        attrValue = []
        #Step 4 attribute name
        while True:
            if c == "=" and attrName:   
                break
            elif c in spaceCharactersBytes:
                #Step 6!
                c = data.skip()
                break
            elif c in ("/", ">"):
                return "".join(attrName), ""
            elif c in asciiUppercaseBytes:
                attrName.append(c.lower())
            elif c == None:
                return None
            else:
                attrName.append(c)
            #Step 5
            c = data.next()
        #Step 7
        if c != "=":
            data.previous()
            return "".join(attrName), ""
        #Step 8
        data.next()
        #Step 9
        c = data.skip()
        #Step 10
        if c in ("'", '"'):
            #10.1
            quoteChar = c
            while True:
                #10.2
                c = data.next()
                #10.3
                if c == quoteChar:
                    data.next()
                    return "".join(attrName), "".join(attrValue)
                #10.4
                elif c in asciiUppercaseBytes:
                    attrValue.append(c.lower())
                #10.5
                else:
                    attrValue.append(c)
        elif c == ">":
            return "".join(attrName), ""
        elif c in asciiUppercaseBytes:
            attrValue.append(c.lower())
        elif c is None:
            return None
        else:
            attrValue.append(c)
        # Step 11
        while True:
            c = data.next()
            if c in spacesAngleBrackets:
                return "".join(attrName), "".join(attrValue)
            elif c in asciiUppercaseBytes:
                attrValue.append(c.lower())
            elif c is None:
                return None
            else:
                attrValue.append(c)
    getAttribute.func_annotations = {}


class ContentAttrParser(object):
    def __init__(self, data):
        assert isinstance(data, str)
        self.data = data
    __init__.func_annotations = {}
    def parse(self):
        try:
            #Check if the attr name is charset 
            #otherwise return
            self.data.jumpTo("charset")
            self.data.position += 1
            self.data.skip()
            if not self.data.currentByte == "=":
                #If there is no = sign keep looking for attrs
                return None
            self.data.position += 1
            self.data.skip()
            #Look for an encoding between matching quote marks
            if self.data.currentByte in ('"', "'"):
                quoteMark = self.data.currentByte
                self.data.position += 1
                oldPosition = self.data.position
                if self.data.jumpTo(quoteMark):
                    return self.data[oldPosition:self.data.position]
                else:
                    return None
            else:
                #Unquoted value
                oldPosition = self.data.position
                try:
                    self.data.skipUntil(spaceCharactersBytes)
                    return self.data[oldPosition:self.data.position]
                except StopIteration:
                    #Return the whole remaining value
                    return self.data[oldPosition:]
        except StopIteration:
            return None
    parse.func_annotations = {}


def codecName(encoding):
    u"""Return the python codec name corresponding to an encoding or None if the
    string doesn't correspond to a valid encoding."""
    if isinstance(encoding, str):
        try:
            encoding = encoding.decode(u"ascii")
        except UnicodeDecodeError:
            return None
    if encoding:
        canonicalName = ascii_punctuation_re.sub(u"", encoding).lower()
        return encodings.get(canonicalName, None)
    else:
        return None
codecName.func_annotations = {}
