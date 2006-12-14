import codecs, StringIO

from constants import EOF

class HTMLInputStream(object):
    """ Provides a unicode stream of characters to the HTMLTokenizer.
    
    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.
    """
    
    def __init__(self, source, encoding=None):
        """ Initialise the HTMLInputReader.
        
        The stream can either be a file-object, filename, url or string
        
        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        
        # Position counters
        self.line = 1
        self.col = 0
        
        # List of where new lines occur
        self.newLines = [0]
        
        # Encoding Information
        self.charEncoding = encoding
        
        # Original Stream
        self.rawStream = self.openStream(source)
        
        # Try to detect the encoding of the stream by looking for a BOM
        detectedEncoding = self.detectEncoding()
        
        # If an encoding was specified or detected from the BOM don't allow
        # the encoding to be changed futher into the stream
        if self.charEncoding or detectedEncoding:
            self.allowEncodingOverride = False
        else:
            self.allowEncodingOverride = True
        
        # If an encoding wasn't specified, use the encoding detected from the
        # BOM, if present, otherwise use the default encoding
        if not self.charEncoding:
            self.charEncoding = detectedEncoding or "cp1252"
        
        # Read bytes from stream decoding them into Unicode
        unicodeStream = self.rawStream.read().decode(self.charEncoding, 'replace')
        
        unicodeStream = self.normalizeStream(unicodeStream)
        
        # If encoding was determined from a BOM remove it from the stream
        if detectedEncoding:
            unicodeStream = unicodeStream[1:]
        
        # Loop through stream and find where new lines occur
        for i in xrange(len(unicodeStream)):
            if unicodeStream[i] == u"\n":
                self.newLines.append(i)
        
        # Turn stream into a file-like object for access to characters
        self.dataStream = StringIO.StringIO(unicodeStream)
    
    def openStream(self, source):
        """ Opens source so it can be used as a file object
        
        Returns a file-like object.
        """
        # Already a file-like object
        if hasattr(source, 'seek'):
            stream = source
        else:
            # Try opening from file system
            try:
                return open(source)
            except: pass
            
            # Otherwise treat source as a string and covert to a file-like object
            stream = StringIO.StringIO(str(source))
        return stream
    
    def detectEncoding(self):
        """ Attempts to detect the character encoding of the stream.
        
        If an encoding can be determined from the BOM return the name of the
        encoding otherwise return None
        """
        
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
        if not encoding:
            encoding = bomDict.get(string[:2])   # UTF-16
            if not encoding:
                encoding = bomDict.get(string)   # UTF-32
        
        # Go back to the beginning of the file
        self.rawStream.seek(0)
        
        return encoding
    
    def normalizeStream(self, stream):
        # Count U+FFFD replacement characters in case we need to switch encoding
        if self.charEncoding == "cp1252" and stream.count(u"\uFFFD"):
            self.incompatibleEncoding = True
        else:
            self.incompatibleEncoding = False
        
        # Normalize new lines
        stream = stream.replace(u"\r\n", u"\n")
        stream = stream.replace(u"\r", u"\n")
        # Replace null bytes
        stream = stream.replace(u"\x00", u"\uFFFD")
        
        return stream
    
    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element
        
        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.
        
        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, return True indicating
        parsing will have to begin again.
        """
        # Only change encoding if we are using the default encoding
        if self.allowEncodingOverride:
            self.charEncoding = encoding
            # If there was incompatible characters found in the first encoding
            # we have to reencode the entire stream and start again
            if self.incompatibleEncoding:
                self.reset()
                self.dataStream = StringIO.StringIO(self.normalizeStream(
                    self.dataStream.read(-1).decode(self.charEncoding, 'replace')
                  ))
                return True
            else:
                # Just decode the bytes from now on
                self.dataStream = codecs.EncodedFile(self.dataStream,
                  self.charEncoding, 'replace')
        return False
    
    def position(self):
        """ Returns (line, col) position in the stream
        """
        line = 0
        tell = self.dataStream.tell()
        for pos in self.newLines:
            if pos < tell:
                line += 1
            else:
                break
        col = tell-self.newLines[line-1]-1
        return (line, col)
    
    def reset(self):
        """ Resets the position in the stream back to the start
        """
        self.dataStream.seek(0)

    def read(self, size=1):
        """ Reads size characters from the stream or EOF if EOF is reached.
        """
        return self.dataStream.read(size) or EOF
    
    def readMany(self, size):
        """ Returns a list of size characters from the stream
        and adds an EOF marker if the EOF is reached.
        """
        charStack = list(self.dataStream.read(size)) or EOF
        if len(charStack) < size:
            charStack.append(EOF)
        return charStack
    
    def readUntil(self, charList):
        """ Returns a list of characters from the stream until a character
        in charList is found or EOF is reached
        """
        charList = set(charList)
        charList.add(EOF)
        
        charStack = [self.read(1)]
        while charStack[-1] not in charList:
            charStack.append(self.read(1))
        
        return charStack
    
    def readWhile(self, charList):
        """ Returns a list of characters from the stream until a character
        not in charList is found or EOF is reached
        """
        charStack = [self.read(1)]
        while charStack[-1] in charList:
            charStack.append(self.read(1))
        
        return charStack

if __name__ == "__main__":
    try:
        stream = HTMLInputStream("tests/utf-8-bom.html")
        
        c = stream.read(1)
        while c:
            line, col = stream.position()
            if c == u"\n":
                print "Line %s, Column %s: Line Feed" % (line, col)
            else:
                print "Line %s, Column %s: %s" % (line, col, c.encode(stream.charEncoding))
            c = stream.read(1)
        print "EOF"
    except IOError:
        print "The file does not exist."
