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

    def __init__(self, source, encoding=None):
        """Initialises the HTMLInputStream.

        HTMLInputStream(source, [encoding]) -> Normalized stream from source
        for use by the HTML5Lib.

        source can be either a file-object, local filename or a string.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)

        """
        # List of where new lines occur
        self.newLines = []

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
            encoding = self.detectEncoding()
        self.charEncoding = encoding

        # Read bytes from stream decoding them into Unicode
        uString = self.rawStream.read().decode(self.charEncoding, 'replace')

        # Normalize new ipythonlines and null characters
        uString = re.sub('\r\n?', '\n', uString)
        uString = re.sub('\x00', u'\uFFFD', uString)

        # Convert the unicode string into a list to be used as the data stream
        self.dataStream = uString

        self.queue = []

        # Reset position in the list to read from
        self.reset()

    def openStream(self, source):
        """Produces a file object from source.

        source can be either a file object, local filename or a string.

        """
        # Already a file object
        if hasattr(source, 'read'):
            stream = source
        else:
            # Otherwise treat source as a string and convert to a file object
            import cStringIO
            stream = cStringIO.StringIO(str(source))
        return stream

    def detectEncoding(self):

        #First look for a BOM
        #This will also read past the BOM if present
        encoding = self.detectBOM()
        #If there is no BOM need to look for meta elements with encoding 
        #information
        if encoding is None:
            encoding = self.detectEncodingMeta()
        #Guess with chardet, if avaliable
        if encoding is None:
            try:
                import chardet
                encoding = chardet.detect(self.rawStream)['encoding']
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
        self.rawStream.seek(0)
        string = self.rawStream.read(4)

        # Try detecting the BOM using bytes from the string
        encoding = bomDict.get(string[:3])       # UTF-8
        seek = 3
        if not encoding:
            encoding = bomDict.get(string[:2])   # UTF-16
            seek = 2
            if not encoding:
                encoding = bomDict.get(string)   # UTF-32
                seek = 4

        #AT - move this to the caller?
        # Set the read position past the BOM if one was found, otherwise
        # set it to the start of the stream
        self.rawStream.seek(encoding and seek or 0)

        return encoding

    def detectEncodingMeta(self):
        """Report the encoding declared by the meta element
        """
        parser = EncodingParser(self.rawStream.read(self.numBytesMeta))
        self.rawStream.seek(0)
        return parser.getEncoding()

    def determineNewLines(self):
        # Looks through the stream to find where new lines occur so
        # the position method can tell where it is.
        self.newLines.append(0)
        for i in xrange(len(self.dataStream)):
            if self.dataStream[i] == u"\n":
                self.newLines.append(i)

    def position(self):
        """Returns (line, col) of the current position in the stream."""
        # Generate list of new lines first time around
        if not self.newLines:
            self.determineNewLines()

        line = 0
        tell = self.tell
        for pos in self.newLines:
            if pos < tell:
                line += 1
            else:
                break
        col = tell - self.newLines[line-1] - 1
        return (line, col)

    def reset(self):
        """Resets the position in the stream back to the start."""
        self.tell = 0

    def char(self):
        """ Read one character from the stream or queue if available. Return
            EOF when EOF is reached.
        """
        if self.queue:
            return self.queue.pop(0)
        else:
            try:
                self.tell += 1
                return self.dataStream[self.tell - 1]
            except:
                return EOF

    def charsUntil(self, characters, opposite = False):
        """ Returns a string of characters from the stream up to but not
        including any character in characters or EOF. characters can be
        any container that supports the in method being called on it.
        """
        charStack = [self.char()]

        # First from the queue
        while charStack[-1] and (charStack[-1] in characters) == opposite \
          and self.queue:
            charStack.append(self.queue.pop(0))

        # Then the rest
        while charStack[-1] and (charStack[-1] in characters) == opposite:
            try:
                self.tell += 1
                charStack.append(self.dataStream[self.tell - 1])
            except:
                charStack.append(EOF)

        # Put the character stopped on back to the front of the queue
        # from where it came.
        self.queue.insert(0, charStack.pop())
        return "".join(charStack)

class EncodingParser(object):
    """Mini parser for detecting character encoding from meta elements"""

    def __init__(self, data):
        """string - the data to work on for encoding detection"""
        self.data = data
        self.position = 0
        self.encoding = None

    def getEncoding(self):
        methodDispatch = (
            ("<!--",self.handleComment),
            ("<meta",self.handleMeta),
            ("</",self.handlePossibleEndTag),
            ("<!",self.handleOther),
            ("<?",self.handleOther),
            ("<",self.handlePossibleStartTag))
        while self.position < len(self.data):
            keepParsing = True
            for key, method in methodDispatch:
                if self.matchBytes(key, lower=True):
                    keepParsing = method()
                    break
            if not keepParsing:
                break
            self.movePosition(1)
        if self.encoding is not None:
            self.encoding = self.encoding.strip()
        return self.encoding

    def readBytes(self, numBytes):
        """Return numBytes bytes from current position in the stream and 
        update the pointer to after those bytes"""
        rv = self.data[self.position:self.position+numBytes]
        self.position += numBytes
        return rv

    def movePosition(self, offset):
        """Move offset bytes from the current read position"""
        self.position += offset

    def matchBytes(self, bytes, lower=False):
        """Look for a sequence of bytes at the start of a string. If the bytes 
        are found return True and advance the position to the byte after the 
        match. Otherwise return False and leave the position alone"""
        data = self.data[self.position:self.position+len(bytes)]
        if lower:
            data = data.lower()
        rv = data.startswith(bytes)
        if rv == True:
            self.movePosition(len(bytes))
        return rv

    def findBytes(self, bytes):
        """Look for the next sequence of bytes matching a given sequence. If
        a match is found advance the position to the last byte of the match
        or to the end of the string"""
        newPosition = self.data[self.position:].find(bytes)
        if newPosition > -1:
            self.position += (newPosition + len(bytes)-1)
            return True
        else:
            self.position = len(self.data)
            return False
    
    def findNext(self, charList):
        """Move the pointer so it points to the next byte in a set of possible
        bytes"""
        while (self.position < len(self.data) and
               self.data[self.position] not in charList):
            self.position += 1

    def handleComment(self):
        """Skip over comments"""
        return self.findBytes("-->")

    def handleMeta(self):
        if self.position == len(self.data):
            #We have <meta at the end of our sniffing stream
            return False
        elif self.data[self.position] not in spaceCharacters:
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
                    contentParser = ContentAttrParser(attr[1])
                    tentativeEncoding = contentParser.parse()
                    self.position += contentParser.position
                    if isValidEncoding(tentativeEncoding):
                        self.encoding = tentativeEncoding    
                        return False

    def handlePossibleStartTag(self):
        return self.handlePossibleTag(False)

    def handlePossibleEndTag(self):     
        return self.handlePossibleTag(True)

    def handlePossibleTag(self, endTag):
        if self.readBytes(1) not in asciiLetters:
            #If the next byte is not an ascii letter either ignore this
            #fragment (possible start tag case) or treat it according to 
            #handleOther
            if endTag:
                self.movePosition(-1)
                self.handleOther()
            else:
                return


        possibleChar =([str(char) for char in spaceCharacters] + 
                        ["<", ">"])
        self.findNext(possibleChar)
        if self.position == len(self.data):
            #If no match is found abort processing
            return False
        elif self.data[self.position] == "<":
            #return to the first step in the overall "two step" algorithm
            self.position -= 1    
            return True
        else:
            #Read all attributes
            attr = self.getAttribute()
            while attr is not None:
                attr = self.getAttribute()
            return True

    def handleOther(self):
        return self.findBytes(">")

    def getAttribute(self):
        """Return a name,value pair for the next attribute in the stream, 
        if one is found, or None"""
        attrParser = AttrParser(self.data[self.position:])
        attr = attrParser.parse()
        self.position += attrParser.position
        #print attr, attrParser.position, self.data[self.position]
        return attr

class FragmentParser(object):
    """Helper object for parsing document fragments e.g. attributes and content
    attribte values"""
    def __init__(self, fragment):
        self.position = 0
        self.fragment = fragment
    
    def parse(self):
        raise NotImplementedError
    
    def skip(self, chars=spaceCharacters):
        while (self.position < len(self.fragment)
               and self.fragment[self.position] in chars):
            self.position += 1
    
    def startsWith(self, value):
        return self.fragment[self.position:].startswith(value)
    
    def findNext(self, charList):
        """Move the pointer so it points to the next byte in a set of possible
        bytes"""
        while (self.position < len(self.fragment) and
               self.fragment[self.position] not in charList):
            self.position += 1

class ContentAttrParser(FragmentParser):
    def parse(self):
        #Skip to the first ";"
        parts = self.fragment.split(";")
        if len(parts) > 1:
            self.fragment = parts[1]
            self.skip()
            #Check if the attr name is charset 
            #otherwise return
            if not self.startsWith("charset"):
                return None
            self.position += len("charset")
            self.skip()
            if not self.fragment[self.position] == "=":
                #If there is no = sign keep looking for attrs
                return None
            self.position += 1
            self.skip()
            #Look for an encoding between matching quote marks
            if self.fragment[self.position] in ('"', "'"):
                quoteMark = self.fragment[self.position]
                self.position += 1
                oldPosition = self.position
                self.findNext(quoteMark)
                if self.position < len(self.fragment):
                    return self.fragment[oldPosition:self.position]
                else:
                    self.position = oldPosition
                    #No matching end quote => no charset
                    return None
            else:
                #Unquoted value
                startPosition = self.position
                self.findNext(spaceCharacters)
                if self.position != len(self.fragment):
                    return self.fragment[startPosition:self.position]
                else:
                    #Return the whole remaining value
                    return self.fragment[startPosition:]
        

class AttrParser(FragmentParser):
    def parse(self):
        self.skip(list(spaceCharacters)+["/"])
        if self.position == len(self.fragment):
            return None
        if self.fragment[self.position] == "<":
            self.position -= 1
            return None
        elif self.fragment[self.position] == ">":
            return None
        attrName = []
        attrValue = []
        spaceFound = False
        #Step 5 attribute name
        while True:
            if self.position == len(self.fragment):
                    return None
            elif self.fragment[self.position] == "=" and attrName:   
                break
            elif self.fragment[self.position] in spaceCharacters:
                spaceFound=True
                break
            elif self.fragment[self.position] in ("/", "<", ">"):
                #self.position -= 1
                return "".join(attrName), ""
            elif self.fragment[self.position] in asciiUppercase:
                attrName.extend(self.fragment[self.position].lower())
            else:
                attrName.extend(self.fragment[self.position])
            #Step 6
            self.position += 1
        #Step 7
        if spaceFound:
            self.skip()
            if self.position == len(self.fragment):
                return "".join(attrName), ""
            #Step 8
            if self.fragment[self.position] != "=":
                self.position -= 1
                return "".join(attrName), ""
        #XXX need to advance positon in both spaces and value case
        #Step 9
        self.position += 1
        #Step 10
        self.skip()
        #XXX Need to exit if we go past the end of the fragment
        if self.position == len(self.fragment):
            return None
        #Step 11
        if self.fragment[self.position] in ("'", '"'):
            #11.1
            quoteChar = self.fragment[self.position]
            while True:
                #11.2
                self.position += 1
                if self.position == len(self.fragment):
                    return None
                #11.3
                elif self.fragment[self.position] == quoteChar:
                    self.position += 1    
                    return "".join(attrName), "".join(attrValue)
                #11.4
                elif self.fragment[self.position] in asciiUppercase:
                    attrValue.extend(self.fragment[self.position].lower())
                #11.5
                else:
                    attrValue.extend(self.fragment[self.position])
        elif self.fragment[self.position] in (">", '<'):
                return "".join(attrName), ""
        elif self.fragment[self.position] in asciiUppercase:
            attrValue.extend(self.fragment[self.position].lower())
        else:
            attrValue.extend(self.fragment[self.position])
        while True:
            self.position +=1
            if self.position == len(self.fragment):
                    return None
            elif self.fragment[self.position] in (
                list(spaceCharacters) + [">", '<']):
                return "".join(attrName), "".join(attrValue)
            elif self.fragment[self.position] in asciiUppercase:
                attrValue.extend(self.fragment[self.position].lower())
            else:
                attrValue.extend(self.fragment[self.position])

def isValidEncoding(encoding):
    """Determine if a string is a supported encoding"""
    return (encoding is not None and type(encoding) == types.StringType and
            encoding.lower().strip() in encodings)
