import codecs
import re
import types

from constants import EOF, spaceCharacters, asciiLetters, asciiUppercase
from constants import encodings
from utils import MethodDispatcher

#Non-unicode versions of constants for use in the pre-parser
spaceCharactersBytes = [str(item) for item in spaceCharacters]
asciiLettersBytes = [str(item) for item in asciiLetters]
asciiUppercaseBytes = [str(item) for item in asciiUppercase]

invalid_unicode_re = re.compile(u"[\u0001-\u0008\u000E-\u001F\u007F-\u009F\uD800-\uDFFF\uFDD0-\uFDDF\uFFFE\uFFFF\U0001FFFE\U0001FFFF\U0002FFFE\U0002FFFF\U0003FFFE\U0003FFFF\U0004FFFE\U0004FFFF\U0005FFFE\U0005FFFF\U0006FFFE\U0006FFFF\U0007FFFE\U0007FFFF\U0008FFFE\U0008FFFF\U0009FFFE\U0009FFFF\U000AFFFE\U000AFFFF\U000BFFFE\U000BFFFF\U000CFFFE\U000CFFFF\U000DFFFE\U000DFFFF\U000EFFFE\U000EFFFF\U000FFFFE\U000FFFFF\U0010FFFE\U0010FFFF]")

ascii_punctuation_re = re.compile(ur"[\u0009-\u000D\u0020-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]")

# Cache for charsUntil()
charsUntilRegEx = {}

class HTMLInputStream(object):
    """Provides a unicode stream of characters to the HTMLTokenizer.

    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.

    """

    _defaultChunkSize = 10240

    def __init__(self, source, encoding=None, parseMeta=True, chardet=True):
        """Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by html5lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        
        parseMeta - Look for a <meta> element containing encoding information

        """
        # List of where new lines occur
        self.newLines = [0]

        self.charEncoding = (codecName(encoding), "certain")

        # Raw Stream - for unicode objects this will encode to utf-8 and set
        #              self.charEncoding as appropriate
        self.rawStream = self.openStream(source)

        # Encoding Information
        #Number of bytes to use when looking for a meta element with
        #encoding information
        self.numBytesMeta = 512
        #Number of bytes to use when using detecting encoding using chardet
        self.numBytesChardet = 100
        #Encoding to use if no other information can be found
        self.defaultEncoding = "windows-1252"
        
        #Detect encoding iff no explicit "transport level" encoding is supplied
        if (self.charEncoding[0] is None):
            self.charEncoding = self.detectEncoding(parseMeta, chardet)

        self.dataStream = codecs.getreader(self.charEncoding[0])(self.rawStream,
                                                                 'replace')

        self.chunk = u""
        self.chunkOffset = 0
        self.ungetBuffer = [] # reversed list of chars from unget()
        self.readChars = []
        self.errors = []

        self.lineLengths = []
        
        #Flag to indicate we may have a CR LF broken across a data chunk
        self._lastChunkEndsWithCR = False

    def openStream(self, source):
        """Produces a file object from source.

        source can be either a file object, local filename or a string.

        """
        # Already a file object
        if hasattr(source, 'read'):
            stream = source
        else:
            # Otherwise treat source as a string and convert to a file object
            if isinstance(source, unicode):
                source = source.encode('utf-8')
                self.charEncoding = ("utf-8", "certain")
            import cStringIO
            stream = cStringIO.StringIO(str(source))
        return stream

    def detectEncoding(self, parseMeta=True, chardet=True):

        #First look for a BOM
        #This will also read past the BOM if present
        encoding = self.detectBOM()
        confidence = "certain"
        #If there is no BOM need to look for meta elements with encoding 
        #information
        if encoding is None and parseMeta:
            encoding = self.detectEncodingMeta()
            confidence = "tentative"
        #Guess with chardet, if avaliable
        if encoding is None and chardet:
            confidence = "tentative"
            try:
                from chardet.universaldetector import UniversalDetector
                buffers = []
                detector = UniversalDetector()
                while not detector.done:
                    buffer = self.rawStream.read(self.numBytesChardet)
                    if not buffer:
                        break
                    buffers.append(buffer)
                    detector.feed(buffer)
                detector.close()
                encoding = detector.result['encoding']
                self.seek("".join(buffers), 0)
            except ImportError:
                pass
        # If all else fails use the default encoding
        if encoding is None:
            confidence="tentative"
            encoding = self.defaultEncoding
        
        #Substitute for equivalent encodings:
        encodingSub = {"iso-8859-1":"windows-1252"}

        if encoding.lower() in encodingSub:
            encoding = encodingSub[encoding.lower()]

        return encoding, confidence

    def detectBOM(self):
        """Attempts to detect at BOM at the start of the stream. If
        an encoding can be determined from the BOM return the name of the
        encoding otherwise return None"""
        bomDict = {
            codecs.BOM_UTF8: 'utf-8',
            codecs.BOM_UTF16_LE: 'utf-16-le', codecs.BOM_UTF16_BE: 'utf-16-be',
            codecs.BOM_UTF32_LE: 'utf-32-le', codecs.BOM_UTF32_BE: 'utf-32-be'
        }

        # Go to beginning of file and read in 4 bytes
        string = self.rawStream.read(4)

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
        self.seek(string, encoding and seek or 0)

        return encoding

    def seek(self, buffer, n):
        """Unget buffer[n:]"""
        if hasattr(self.rawStream, 'unget'):
            self.rawStream.unget(buffer[n:])
            return 

        if hasattr(self.rawStream, 'seek'):
            try:
                self.rawStream.seek(n)
                return
            except IOError:
                pass

        class BufferedStream:
             def __init__(self, data, stream):
                 self.data = data
                 self.stream = stream
             def read(self, chars=-1):
                 if chars == -1 or chars > len(self.data):
                     result = self.data
                     self.data = ''
                     if chars == -1:
                         return result + self.stream.read()
                     else:
                         return result + self.stream.read(chars-len(result))
                 elif not self.data:
                     return self.stream.read(chars)
                 else:
                     result = self.data[:chars]
                     self.data = self.data[chars:]
                     return result
             def unget(self, data):
                 if self.data:
                     self.data += data
                 else:
                     self.data = data

        self.rawStream = BufferedStream(buffer[n:], self.rawStream)

    def detectEncodingMeta(self):
        """Report the encoding declared by the meta element
        """
        buffer = self.rawStream.read(self.numBytesMeta)
        parser = EncodingParser(buffer)
        self.seek(buffer, 0)
        encoding = parser.getEncoding()
        return encoding

    def updatePosition(self):
        #Remove EOF from readChars, if present
        if not self.readChars:
            return
        if self.readChars and self.readChars[-1] == EOF:
            #There may be more than one EOF in readChars so we cannot assume
            #readChars.index(EOF) == -1
            self.readChars = self.readChars[:self.readChars.index(EOF)]
        readChars = "".join(self.readChars)
        lines = readChars.split("\n")
        if self.lineLengths:
            self.lineLengths[-1] += len(lines[0])
        else:
            self.lineLengths.append(len(lines[0]))
        for line in lines[1:]:
            self.lineLengths.append(len(line))
        self.readChars = []
        #print self.lineLengths

    def position(self):
        """Returns (line, col) of the current position in the stream."""
        self.updatePosition()
        if self.lineLengths:
            line, col = len(self.lineLengths), self.lineLengths[-1]
        else:
            line, col = 1,0
        return (line, col)

    def char(self):
        """ Read one character from the stream or queue if available. Return
            EOF when EOF is reached.
        """
        if self.ungetBuffer:
            char = self.ungetBuffer.pop()
            self.readChars.append(char)
            return char

        if self.chunkOffset >= len(self.chunk):
            if not self.readChunk():
                return EOF

        char = self.chunk[self.chunkOffset]
        self.chunkOffset += 1

        self.readChars.append(char)
        return char

    def readChunk(self, chunkSize=_defaultChunkSize):
        self.chunk = u""
        self.chunkOffset = 0

        data = self.dataStream.read(chunkSize)
        if not data:
            return False
        #Replace null characters
        for i in xrange(data.count(u"\u0000")):
            self.errors.append("null-character")
        for i in xrange(len(invalid_unicode_re.findall(data))):
            self.errors.append("invalid-codepoint")

        data = data.replace(u"\u0000", u"\ufffd")
        #Check for CR LF broken across chunks
        if (self._lastChunkEndsWithCR and data[0] == "\n"):
            data = data[1:]
            # Stop if the chunk is now empty
            if not data:
                return False
        self._lastChunkEndsWithCR = data[-1] == "\r"
        data = data.replace("\r\n", "\n")
        data = data.replace("\r", "\n")

        data = unicode(data)
        self.chunk = data

        self.updatePosition()
        return True

    def charsUntil(self, characters, opposite = False):
        """ Returns a string of characters from the stream up to but not
        including any character in 'characters' or EOF. 'characters' must be
        a container that supports the 'in' method and iteration over its
        characters.
        """

        rv = []

        # The unget buffer is typically small and rarely used, so
        # just check each character individually
        while self.ungetBuffer:
            if self.ungetBuffer[-1] == EOF or (self.ungetBuffer[-1] in characters) != opposite:
                r = u"".join(rv)
                self.readChars.extend(list(r))
                return r
            else:
                rv.append(self.ungetBuffer.pop())

        # Use a cache of regexps to find the required characters
        try:
            chars = charsUntilRegEx[(characters, opposite)]
        except KeyError:
            for c in characters: assert(ord(c) < 128)
            regex = u"".join(["\\x%02x" % ord(c) for c in characters])
            if not opposite:
                regex = u"^%s" % regex
            chars = charsUntilRegEx[(characters, opposite)] = re.compile(u"[%s]*" % regex)

        while True:
            # Find the longest matching prefix
            m = chars.match(self.chunk, self.chunkOffset)
            # If not everything matched, return everything up to the part that didn't match
            end = m.end()
            if end != len(self.chunk):
                rv.append(self.chunk[self.chunkOffset:end])
                self.chunkOffset = end
                break
            # If the whole chunk matched, use it all and read the next chunk
            rv.append(self.chunk[self.chunkOffset:])
            if not self.readChunk():
                # Reached EOF
                break

        r = u"".join(rv)
        self.readChars.extend(list(r))
        return r

    def unget(self, chars):
        self.updatePosition()
        if chars:
            l = list(chars)
            l.reverse()
            self.ungetBuffer.extend(l)
            #Alter the current line, col position
            for c in chars[::-1]:
                if c is None:
                    continue
                elif c == '\n':
                    assert self.lineLengths[-1] == 0
                    self.lineLengths.pop()
                else:
                    self.lineLengths[-1] -= 1

class EncodingBytes(str):
    """String-like object with an assosiated position and various extra methods
    If the position is ever greater than the string length then an exception is
    raised"""
    def __init__(self, value):
        str.__init__(self, value)
        self._position=-1
    
    def __iter__(self):
        return self
    
    def next(self):
        self._position += 1
        rv = self[self.position]
        return rv
    
    def setPosition(self, position):
        if self._position >= len(self):
            raise StopIteration
        self._position = position
    
    def getPosition(self):
        if self._position >= len(self):
            raise StopIteration
        if self._position >= 0:
            return self._position
        else:
            return None
    
    position = property(getPosition, setPosition)

    def getCurrentByte(self):
        return self[self.position]
    
    currentByte = property(getCurrentByte)

    def skip(self, chars=spaceCharactersBytes):
        """Skip past a list of characters"""
        while self.currentByte in chars:
            self.position += 1

    def matchBytes(self, bytes, lower=False):
        """Look for a sequence of bytes at the start of a string. If the bytes 
        are found return True and advance the position to the byte after the 
        match. Otherwise return False and leave the position alone"""
        data = self[self.position:self.position+len(bytes)]
        if lower:
            data = data.lower()
        rv = data.startswith(bytes)
        if rv == True:
            self.position += len(bytes)
        return rv
    
    def jumpTo(self, bytes):
        """Look for the next sequence of bytes matching a given sequence. If
        a match is found advance the position to the last byte of the match"""
        newPosition = self[self.position:].find(bytes)
        if newPosition > -1:
            self._position += (newPosition + len(bytes)-1)
            return True
        else:
            raise StopIteration
    
    def findNext(self, byteList):
        """Move the pointer so it points to the next byte in a set of possible
        bytes"""
        while (self.currentByte not in byteList):
            self.position += 1

class EncodingParser(object):
    """Mini parser for detecting character encoding from meta elements"""

    def __init__(self, data):
        """string - the data to work on for encoding detection"""
        self.data = EncodingBytes(data)
        self.encoding = None

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
                if self.data.matchBytes(key, lower=True):
                    try:
                        keepParsing = method()    
                        break
                    except StopIteration:
                        keepParsing=False
                        break
            if not keepParsing:
                break
        if self.encoding is not None:
            self.encoding = self.encoding.strip()        
            #Spec violation that complies with hsivonen + mjs
            if (ascii_punctuation_re.sub("", self.encoding) in
                ("utf16", "utf16be", "utf16le",
                 "utf32", "utf32be", "utf32le")):
                self.encoding = "utf-8"
        
        return self.encoding

    def handleComment(self):
        """Skip over comments"""
        return self.data.jumpTo("-->")

    def handleMeta(self):
        if self.data.currentByte not in spaceCharactersBytes:
            #if we have <meta not followed by a space so just keep going
            return True
        #We have a valid meta element we want to search for attributes
        while True:
            #Try to find the next attribute after the current position
            attr = self.getAttribute()
            if attr is None:
                return True
            else:
                if attr[0] == "charset":
                    tentativeEncoding = attr[1]
                    codec = codecName(tentativeEncoding)
                    if codec is not None:
                        self.encoding = codec
                        return False
                elif attr[0] == "content":
                    contentParser = ContentAttrParser(EncodingBytes(attr[1]))
                    tentativeEncoding = contentParser.parse()
                    codec = codecName(tentativeEncoding)
                    if codec is not None:
                        self.encoding = codec
                        return False

    def handlePossibleStartTag(self):
        return self.handlePossibleTag(False)

    def handlePossibleEndTag(self):
        self.data.position+=1
        return self.handlePossibleTag(True)

    def handlePossibleTag(self, endTag):
        if self.data.currentByte not in asciiLettersBytes:
            #If the next byte is not an ascii letter either ignore this
            #fragment (possible start tag case) or treat it according to 
            #handleOther
            if endTag:
                self.data.position -= 1
                self.handleOther()
            return True
        
        self.data.findNext(list(spaceCharactersBytes) + ["<", ">"])
        if self.data.currentByte == "<":
            #return to the first step in the overall "two step" algorithm
            #reprocessing the < byte
            self.data.position -= 1    
        else:
            #Read all attributes
            attr = self.getAttribute()
            while attr is not None:
                attr = self.getAttribute()
        return True

    def handleOther(self):
        return self.data.jumpTo(">")

    def getAttribute(self):
        """Return a name,value pair for the next attribute in the stream, 
        if one is found, or None"""
        self.data.skip(list(spaceCharactersBytes)+["/"])
        if self.data.currentByte == "<":
            self.data.position -= 1
            return None
        elif self.data.currentByte == ">":
            return None
        attrName = []
        attrValue = []
        spaceFound = False
        #Step 5 attribute name
        while True:
            if self.data.currentByte == "=" and attrName:   
                break
            elif self.data.currentByte in spaceCharactersBytes:
                spaceFound=True
                break
            elif self.data.currentByte in ("/", "<", ">"):
                return "".join(attrName), ""
            elif self.data.currentByte in asciiUppercaseBytes:
                attrName.extend(self.data.currentByte.lower())
            else:
                attrName.extend(self.data.currentByte)
            #Step 6
            self.data.position += 1
        #Step 7
        if spaceFound:
            self.data.skip()
            #Step 8
            if self.data.currentByte != "=":
                self.data.position -= 1
                return "".join(attrName), ""
        #XXX need to advance position in both spaces and value case
        #Step 9
        self.data.position += 1
        #Step 10
        self.data.skip()
        #Step 11
        if self.data.currentByte in ("'", '"'):
            #11.1
            quoteChar = self.data.currentByte
            while True:
                self.data.position+=1
                #11.3
                if self.data.currentByte == quoteChar:
                    self.data.position += 1
                    return "".join(attrName), "".join(attrValue)
                #11.4
                elif self.data.currentByte in asciiUppercaseBytes:
                    attrValue.extend(self.data.currentByte.lower())
                #11.5
                else:
                    attrValue.extend(self.data.currentByte)
        elif self.data.currentByte in (">", "<"):
                return "".join(attrName), ""
        elif self.data.currentByte in asciiUppercaseBytes:
            attrValue.extend(self.data.currentByte.lower())
        else:
            attrValue.extend(self.data.currentByte)
        while True:
            self.data.position +=1
            if self.data.currentByte in (
                list(spaceCharactersBytes) + [">", "<"]):
                return "".join(attrName), "".join(attrValue)
            elif self.data.currentByte in asciiUppercaseBytes:
                attrValue.extend(self.data.currentByte.lower())
            else:
                attrValue.extend(self.data.currentByte)


class ContentAttrParser(object):
    def __init__(self, data):
        self.data = data
    def parse(self):
        try:
            #Skip to the first ";"
            self.data.jumpTo(";")
            self.data.position += 1
            self.data.skip()
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
                self.data.jumpTo(quoteMark)
                return self.data[oldPosition:self.data.position]
            else:
                #Unquoted value
                oldPosition = self.data.position
                try:
                    self.data.findNext(spaceCharactersBytes)
                    return self.data[oldPosition:self.data.position]
                except StopIteration:
                    #Return the whole remaining value
                    return self.data[oldPosition:]
        except StopIteration:
            return None

def codecName(encoding):
    """Return the python codec name corresponding to an encoding or None if the
    string doesn't correspond to a valid encoding."""
    if (encoding is not None and type(encoding) == types.StringType):
        canonicalName = ascii_punctuation_re.sub("", encoding).lower()
        return encodings.get(canonicalName, None) 
    else:
        return None
