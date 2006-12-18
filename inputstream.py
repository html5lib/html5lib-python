import codecs, re

from constants import EOF

class HTMLInputStream(object):
    """ Provides a unicode stream of characters to the HTMLTokenizer.
    
    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.
    """
    
    def __init__(self, source, encoding=None):
        """ Initialise the HTMLInputStream.
        
        The source can either be a file-object, filename, url or string
        
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
        self.rawStream = self.openStream(source)
        
        # Try to detect the encoding of the stream by looking for a BOM
        detectedEncoding = self.detectEncoding()
        
        # Note whether a BOM needs to be skipped over
        self.skipBOM = detectedEncoding and 1 or 0
        
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
        uString = self.rawStream.read().decode(self.charEncoding, 'replace')
        
        # Normalize new lines and null characters
        uString = re.sub('\r\n?', '\n', uString)
        uString = re.sub('\x00', '\xFFFD', uString)
        
        uList = list(uString)
        
        # Reset position in the list to read from
        self.reset()
        
        # Loop through stream and find where new lines occur
        for i in xrange(self.tell, len(uList)):
            if uList[i] == u"\n":
                self.newLines.append(i)
        
        # Use the normalized unicode list as the data stream
        self.dataStream = uList
    
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
            import cStringIO
            stream = cStringIO.StringIO(str(source))
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
        tell = self.tell
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
        self.tell = self.skipBOM or 0

    def read(self, size=1):
        """ Reads size characters from the stream or EOF if EOF is reached.
        """
        try:
            self.tell += 1
            return self.dataStream[self.tell-1]
        except:
            return None

if __name__ == "__main__":
    try:
        stream = HTMLInputStream("tests/utf-8-bom.html")
        
        c = stream.read(1)
        while c:
            line, col = stream.position()
            if c == u"\n":
                print "Line %s, Column %s: Line Feed" % (line, col)
            else:
                print "Line %s, Column %s: %s" % (line, col, c.encode('utf-8'))
            c = stream.read(1)
        print "EOF"
    except IOError:
        print "The file does not exist."
