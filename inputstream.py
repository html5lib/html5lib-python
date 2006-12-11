import codecs, StringIO

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
        # Normalize new lines
        unicodeStream = unicodeStream.replace(u"\r\n", u"\n")
        unicodeStream = unicodeStream.replace(u"\r", u"\n")
        # Replace null bytes
        unicodeStream = unicodeStream.replace(u"\x00", u"\uFFFD")
        
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
    
    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element
        
        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.
        
        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, return True indicating
        parsing will have to begin again.
        """
        pass
    
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
    
    def read(self, size=1):
        """ Read at most size characters from the stream
        """
        char = self.dataStream.read(size)
        return char
    
    def readMany(self, size):
        """ Reads multiple characters from the stream returning a list
        """
        charStack = []
        charStack.append(list(self.dataStream.read(size)))
        
        if len(charStack) < size:
            charStack.append(None)
        
        return charStack
    
    def readUntil(self, charList):
        """ Returns a list of characters from the stream until a character
        in charList is found or EOF is reached
        """
        charStack = [self.dataStream.read(1) or None]
        while charStack[-1] and charStack[-1] not in charList:
            charStack.append(self.dataStream.read(1) or None)
        return charStack

if __name__ == "__main__":
    try:
        # Hard coded file name for now, this will need to be fixed later
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
