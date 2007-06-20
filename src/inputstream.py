import codecs
import re
import types

from constants import EOF, spaceCharacters, asciiLetters, asciiUppercase
from constants import encodings
from utils import MethodDispatcher

class HTMLInputStream(object):
    """Provides a unicode stream of characters to the HTMLTokenizer.

    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.

    """

    def __init__(self, source, encoding=None, parseMeta=True, chardet=True):
        """Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by the HTML5Lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        
        parseMeta - Look for a <meta> element containing encoding information

        """
        # List of where new lines occur
        self.newLines = [0]

        # Raw Stream
        self.rawStream = self.openStream(source)

        # Encoding Information
        #Number of bytes to use when looking for a meta element with
        #encoding information
        self.numBytesMeta = 512
        #Encoding to use if no other information can be found
        self.defaultEncoding = "windows-1252"
        
        #Detect encoding iff no explicit "transport level" encoding is supplied
        if encoding is None or not isValidEncoding(encoding):
            encoding = self.detectEncoding(parseMeta, chardet)
        self.charEncoding = encoding

        self.dataStream = codecs.getreader(self.charEncoding)(self.rawStream, 'replace')

        self.queue = []

        self.line = self.col = 0
        self.lineLengths = []

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
            import cStringIO
            stream = cStringIO.StringIO(str(source))
        return stream

    def detectEncoding(self, parseMeta=True, chardet=True):

        #First look for a BOM
        #This will also read past the BOM if present
        encoding = self.detectBOM()
        #If there is no BOM need to look for meta elements with encoding 
        #information
        if encoding is None and parseMeta:
            encoding = self.detectEncodingMeta()
        #Guess with chardet, if avaliable
        if encoding is None and chardet:
            try:
                import chardet
                buffer = self.rawStream.read()
                encoding = chardet.detect(buffer)['encoding']
                self.seek(buffer, 0)
            except ImportError:
                pass
        # If all else fails use the default encoding
        if encoding is None:
            encoding = self.defaultEncoding
        
        #Substitute for equivalent encodings:
        encodingSub = {"iso-8859-1":"windows-1252"}

        if encoding.lower() in encodingSub:
            encoding = encodingSub[encoding.lower()]

        return encoding

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
        return parser.getEncoding()

    def position(self):
        """Returns (line, col) of the current position in the stream."""
        line, col = self.line, self.col
        for c in self.queue[::-1]:
            if c == '\n':
                line -= 1
                assert col == 0
                col = self.lineLengths[line]
            else:
                col -= 1
        return (line + 1, col)

    def char(self):
        """ Read one character from the stream or queue if available. Return
            EOF when EOF is reached.
        """
        if self.queue:
            return self.queue.pop(0)
        else:
            c = self.dataStream.read(1, 1)
            if not c:
                self.col += 1
                return EOF

            # Normalize newlines and null characters
            if c == '\x00': c = u'\uFFFD'
            if c == '\r':
                c = self.dataStream.read(1, 1)
                if c != '\n':
                    self.queue.insert(0, unicode(c))
                c = '\n'

            # update position in stream
            if c == '\n':
                self.lineLengths.append(self.col)
                self.line += 1
                self.col = 0
            else:
                self.col += 1
            return unicode(c)

    def charsUntil(self, characters, opposite = False):
        """ Returns a string of characters from the stream up to but not
        including any character in characters or EOF. characters can be
        any container that supports the in method being called on it.
        """
        charStack = [self.char()]

        while charStack[-1] and (charStack[-1] in characters) == opposite:
            charStack.append(self.char())

        # Put the character stopped on back to the front of the queue
        # from where it came.
        c = charStack.pop()
        if c != EOF:
            self.queue.insert(0, c)
        
        return u"".join(charStack)

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

    def skip(self, chars=spaceCharacters):
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
        return self.encoding

    def handleComment(self):
        """Skip over comments"""
        return self.data.jumpTo("-->")

    def handleMeta(self):
        if self.data.currentByte not in spaceCharacters:
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
                    if isValidEncoding(tentativeEncoding):
                        self.encoding = tentativeEncoding    
                        return False
                elif attr[0] == "content":
                    contentParser = ContentAttrParser(EncodingBytes(attr[1]))
                    tentativeEncoding = contentParser.parse()
                    if isValidEncoding(tentativeEncoding):
                        self.encoding = tentativeEncoding    
                        return False

    def handlePossibleStartTag(self):
        return self.handlePossibleTag(False)

    def handlePossibleEndTag(self):
        self.data.position+=1
        return self.handlePossibleTag(True)

    def handlePossibleTag(self, endTag):
        if self.data.currentByte not in asciiLetters:
            #If the next byte is not an ascii letter either ignore this
            #fragment (possible start tag case) or treat it according to 
            #handleOther
            if endTag:
                self.data.position -= 1
                self.handleOther()
            return True
        
        self.data.findNext(list(spaceCharacters) + ["<", ">"])
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
        self.data.skip(list(spaceCharacters)+["/"])
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
            elif self.data.currentByte in spaceCharacters:
                spaceFound=True
                break
            elif self.data.currentByte in ("/", "<", ">"):
                return "".join(attrName), ""
            elif self.data.currentByte in asciiUppercase:
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
                elif self.data.currentByte in asciiUppercase:
                    attrValue.extend(self.data.currentByte.lower())
                #11.5
                else:
                    attrValue.extend(self.data.currentByte)
        elif self.data.currentByte in (">", '<'):
                return "".join(attrName), ""
        elif self.data.currentByte in asciiUppercase:
            attrValue.extend(self.data.currentByte.lower())
        else:
            attrValue.extend(self.data.currentByte)
        while True:
            self.data.position +=1
            if self.data.currentByte in (
                list(spaceCharacters) + [">", '<']):
                return "".join(attrName), "".join(attrValue)
            elif self.data.currentByte in asciiUppercase:
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
                    self.data.findNext(spaceCharacters)
                    return self.data[oldPosition:self.data.position]
                except StopIteration:
                    #Return the whole remaining value
                    return self.data[oldPosition:]
        except StopIteration:
            return None

def isValidEncoding(encoding):
    """Determine if a string is a supported encoding"""
    return (encoding is not None and type(encoding) == types.StringType and
            encoding.lower().strip() in encodings)
