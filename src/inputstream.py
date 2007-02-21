import codecs
import re

from constants import EOF, spaceCharacters, asciiLetters, asciiUppercase
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
        #Encoding to use if no other information can be found
        self.defaultEncoding = "cp1252"
        #Detect encoding iff no explicit "transport level" encoding is supplied
        if encoding is None:
            encoding = self.detectEncoding()
        self.charEncoding = encoding

        # Read bytes from stream decoding them into Unicode
        uString = self.rawStream.read().decode(self.charEncoding, 'replace')

        # Normalize new lines and null characters
        uString = re.sub('\r\n?', '\n', uString)
        uString = re.sub('\x00', '\xFFFD', uString)

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
        if encoding is not None:
            return encoding

        #If there is no BOM need to look for meta elements with encoding 
        #information
        #encoding = self.detectEncodingMeta()
        #if encoding is not None:
        #    return encoding

        #Guess with chardet, if avaliable
        try:
            import chardet
            return chardet.detect(self.rawStream)['encoding']
        except ImportError:
            pass

        # If all else fails use the default encoding
        return self.defaultEncoding

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

    def detectEncodingMeta(self, encoding):
        """Report the encoding declared by the meta element
        """
        parser = MetaParser(self.rawStream.read(self.numBytesMeta))
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

    def __init__(self, inputStream, string):
        """string - the data to work on for encoding detection"""
        self.inputStream = inputStream
        self.data = data
        self.position = 0
        self.encoding = None

    def getEncoding(self):
        methodDispatch = (
            ("<!--",self.handleComment),
            ("<meta",self.handleMeta),
            ("</",self.handlePossibleEndTag),
            ("<!",self.handleOther)
            ("<?",self.handleOther),
            ("<",handlePossibleStartTag))
        while self.position < len(self.data):
            keepParsing = True
            for key, method in unparsedData:
                if self.matchBytes(key):
                    self.movePosition(len(key))
                    keepParsing = method()
                    break
            if not keepParsing:
                break
            self.movePosition(1)
        return self.encoding

    def readBytes(self, numBytes):
        """Return numBytes bytes from current position in the stream and 
        update the pointer to after those bytes"""
        rv = self.data[self.position:self.position+numBytes]
        self.position += numBytes
        return rv

    def movePosition(self, offset):
        """Move offset bytes from the current read position"""
        self.positon += offset

    def matchBytes(self, bytes):
        """Look for a sequence of bytes at the start of a string. If the bytes 
        are found return True and advance the position to the byte after the 
        match. Otherwise return False and leave the position alone"""
        rv = self.data[self.position:].startswith(bytes)
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

    def handleComment(self):
        """Skip over comments"""
        return self.findBytes("-->")

    def handleMeta(self):
        if self.position == len(self.data)-1:
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
                    if self.isValidEncoding(tentativeEncoding):
                        self.encoding = tentativeEncoding    
                        return False
                elif attr[0] == "content":
                    contentParser = ContentAttrParser(attr[1])
                    tentativeEncoding = contentParser.parse()
                    if self.isValidEncoding(tentativeEncoding):
                        self.encoding = tentativeEncoding    
                        return False

    def handlePossibleStartTag(self):
        return self.handlePossibleTag(self, False)

    def handlePossibleEndTag(self):     
        return self.handlePossibleTag(self, True)

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

        startPosition = position
        match = False
        for possibleChar in ([str(char) for char in spaceCharacters] + 
                             ["<", ">"]):
            if self.findBytes(possibleChar):
                match = True
                break
            else:
                self.position = startPosition
        if not match:
            #If no match is found set the position to the end of the data
            self.position = len(self.data)
            return False
        else:
            #Read all attributes
            self.getAttribute()
            while attr is not None:
                self.getAttribute()
            return True

    def handleOther(self):
        return self.findBytes(">")

    def getAttribute(self):
        """Return a name,value pair for the next attribute in the stream, 
        if one is found, or None"""
        attrParser = AttrParser(self.data[self.position:])
        attr = attrParser.parse()
        self.position += attrParser.position
        return attr

    def isValidEncodinfEncoding(self, encoding):
        """Determine if encoding is a valid encoding and, if it is, set it 
        as the encoding on the inputstream"""
        #XXX to do
        try:
            codecs.lookup(encoding)
            rv = True
        except codecs.LookupError:
            rv = False
        return rv

class FragmentParser(object):
    """Helper object for parsing document fragments e.g. attributes and content
    attribte values"""
    def __init__(self, fragment):
        self.position = 0
        self.fragment = fragment
    
    def parse(self):
        raise NotImplementedError
    
    def skip(self, chars=spaceCharacters):
        while self.fragment[self.position] in chars:
            self.position += 1
    
    def startsWith(self, value):
        return self.fragment[self.position:].startswith(value)
    
    def findBytes(self, bytes):
        """Look for the next sequence of bytes matching a given sequence. If
        a match is found advance the position to the last byte of the match or
        to the end of the string"""
        newPosition = self.fragment[self.position:].find(bytes)
        if newPosition > -1:
            self.position += (newPosition + len(bytes)-1)
            return True
        else:
            self.position = len(self.data)
            return False
        
class ContentAttrParser(FragmentParser):
    def parse(self):
        #Skip to the first ";"
        parts = self.fragment.split(";")
        if len(parts) > 1:
            self.value = parts[1]
            self.skipWhitespace()
            #Check if the attr name is charset 
            #otherwise return
            if self.startsWith("charset"):
                return None
            self.position += len("charset")
            self.skip()
            if not self.fragment[self.position] == "=":
                #If there is no = sign keep looking for attrs
                return None
            self.position += 1
            self.skip()
            #Look for an encoding between matching quote marks
            if value[position] in ('"', "'"):
                quoteMark = value[position]
                self.position += 1
                oldPosition = self.positon
                endQuotePosition = selfBytes(quoteMark)
                if endQuotePosition > -1:
                    return value[position:position+endQuotePosition]
                else:
                    self.position = oldPosition
                    #No matching end quote => no charset
                    return None
            else:
                #Unquoted value
                for char in spaceCharacters:
                    oldPosition = self.position
                    self.findByte(char) 
                    if self.position > -1:
                        return value[position:position+spacePosition]
                    else:
                        self.position = oldPosition
                #Return the whole remaining value
                return value[position:]
            
    class AttrParser(FragmentParser):
        def parse(self):
            self.skip(list(spaceCharacters)+["/"])
            if self.value[self.position] == "<":
                self.position -= 1
                return None
            elif self.value[self.position] == "<":
                return None
            attrName = []
            attrValue = []
            spaceFound = False
            while True:
                if self.fragment[self.position] == "=" and attrName:   
                    break
                elif self.fragment[self.position] in spaceCharacters:
                    spaceFound=True
                    break
                elif self.fragment[self.position] in ("/", "<", ">"):
                    self.position -= 1
                    return "".join(attrName), ""
                elif self.fragment[self.position] in asciiUppercase:
                    attrName.extend(self.fragment[self.position].lower())
                else:
                    attrName.extend(self.fragment[self.position])
                self.position += 1
            if spaceFound:
                self.skip()
                if self.fragment[self.position] != "=":
                    self.position -= 1
                    return "".join(attrName), ""
                self.position += 1
            self.skip()
            if self.fragment[self.position] in ("'", '"'):
                quoteChar = self.fragment[self.position]
                self.position += 1
                while True:
                    if self.fragment[self.position] == quoteChar:
                        return "".join(attrName), "".join(attrValue)
                    elif self.fragment[self.position] in asciiUppercase:
                        attrName.extend(self.fragment[self.position].lower())
                    else:
                        attrName.extend(self.fragment[self.position])
            elif self.fragment[self.position] in (">", '<'):
                    self.position -= 1
                    return "".join(attrName), ""
            elif self.fragment[self.position] in asciiUppercase:
                attrName.extend(self.fragment[self.position].lower())
            else:
                attrName.extend(self.fragment[self.position])
            #XXX I think this next bit is right but there is a bug in the spec
            while True:
                self.position +=1
                if self.fragment[self.position] in (
                    list(spaceCharacters).extend([">", '<'])):
                    self.position -= 1
                    return "".join(attrName), ""
                elif self.fragment[self.position] in asciiUppercase:
                    attrName.extend(self.fragment[self.position].lower())
                else:
                    attrName.extend(self.fragment[self.position])
