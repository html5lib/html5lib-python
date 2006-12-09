import codecs, StringIO

class HTMLInputStream(object):
    """ Provides a unicode stream of characters to the HTMLTokenizer.
    
    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.
    """
    
    def __init__(self, stream, encoding=None):
        """ Initialise the HTMLInputReader.
        
        The stream can either be a file-object, filename, url or string
        
        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        
        # List of where new lines occur
        self.newLines = [0]
        
        # Encoding Information
        self.charEncoding = encoding
        
        # Original Stream
        self.stream = self.openStream(stream)
        
        # Try to detect the encoding of the stream by looking for a BOM
        encoding = self.detectEncoding()
        
        # If an encoding was specified or detected from the BOM don't allow
        # the encoding to be changed futher into the stream
        if self.charEncoding or encoding:
            self.allowEncodingOverride = False
        else:
            self.allowEncodingOverride = True
            self.characterError = False
        
        # If an encoding wasn't specified, use the encoding detected from the
        # BOM, if present, otherwise use the default encoding
        if not self.charEncoding:
            self.charEncoding = encoding or "cp1252"
        
        # Read bytes from stream decoding them into Unicode
        unicodeStream = self.stream.read().decode(self.charEncoding, 'replace')
        # Normalize new lines
        unicodeStream = unicodeStream.replace(u"\r\n", u"\n")
        unicodeStream = unicodeStream.replace(u"\r", u"\n")
        # Replace null bytes
        unicodeStream = unicodeStream.replace(u"\x00", u"\uFFFD")
        
        # If encoding was determined from a BOM remove it from the stream
        if encoding:
            unicodeStream = unicodeStream[1:]
            
        # Turn stream into a file-like object for access to characters
        self.encodedStream = StringIO.StringIO(unicodeStream)
        
        # Loop through stream and find where new lines occur
        for i in xrange(len(unicodeStream)):
            if unicodeStream[i] == u"\n":
                self.newLines.append(i)
    
    def openStream(self, stream):
        """ Opens stream first trying the native open function, if that
        fails try to open as a URL and finally treating stream as a string.
        
        Returns a file-like object.
        """
        # Already a file-like object?
        if hasattr(stream, 'seek'):
            return stream
        
        # Try opening stream normally
        try:
            return open(stream)
        except: pass
        
        # Otherwise treat stream as a string and covert to a file-like object
        import StringIO as StringIO
        return StringIO.StringIO(str(stream))
    
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
        self.stream.seek(0)
        string = self.stream.read(4)
        
        # Try detecting the BOM using bytes from the string
        encoding = bomDict.get(string[:3])       # UTF-8
        if not encoding:
            encoding = bomDict.get(string[:2])   # UTF-16
            if not encoding:
                encoding = bomDict.get(string)   # UTF-32
        
        # Go back to the beginning of the file
        self.stream.seek(0)
        
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
        tell = self.tell()
        for pos in self.newLines:
            if pos < tell:
                line += 1
            else:
                break
        col = tell-self.newLines[line-1]-1
        return (line, col)
    
    def seek(self, offset, whence=0):
        self.encodedStream.seek(offset, whence)
    
    def tell(self):
        return self.encodedStream.tell()
    
    def read(self, size=1, stopAt=None):
        """ Read at most size characters from the stream stopping when
        encountering a character in stopAt if supplied.
        
        stopAt can be any iterable object such as a string, list or tuple.
        """
        
        # If stopAt not specified just return the characters asked for
        if not stopAt:
            return self.encodedStream.read(size)
        else:
            # Keep reading characters until we reach on that is in stopAt
            charStack = [self.encodedStream.read(1)]
            while charStack[-1] not in stopAt:
                charStack.append(self.encodedStream.read(1))
            return "".join(charStack)
    
    def readUntil(self, charList):
        """ Returns a string of characters from the stream until a character
        in charList is found or EOF is reached
        """
        return self.read(stopAt=charList)
    
    def lookAhead(self, amount):
        """ Returns the amount of characters specified without moving
        forward within the stream.
        """
        cp = self.encodedStream.tell()
        string = self.read(amount)
        self.seek(cp)
        return string

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
