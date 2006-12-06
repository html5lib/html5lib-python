class HTMLInputStream(object):
    """For reading data from an input stream

    This deals with character encoding issues automatically.    
    """

    def __init__(self, file):
        self.__file = file
        self.__line = 1 # Current line number
        self.__col = 0  # Current column number

        self.__charEncoding = self.__detectBOM(file)

        if self.__charEncoding:
            # The encoding is known from the BOM, don't allow later
            # declarations from the meta element to override this.
            self.__allowEncodingOverride = False
        else:
            self.__allowEncodingOverride = True
            self.__charEncoding = "cp1252" # default to Windows-1252

        # Read the first line
        self.__srcLine = unicode(self.__file.readline(), self.__charEncoding)

        # Strip the BOM, if present
        self.__srcLine = self.__srcLine.lstrip(u"\uFEFF")

    # private function
    def __detectBOM(self, fp):
        """ Attempts to detect the character encoding of the html file
        given by a file object fp. fp must not be a codec wrapped file
        object!

        The return value can be:
            - if detection of the BOM succeeds, the codec name of the
              corresponding unicode charset is returned

            - if BOM detection fails, None is returned.
        """
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/363841

        ### detection using BOM
        
        ## the BOMs we know, by their pattern
        bomDict = { # bytepattern : name              
                   (0x00, 0x00, 0xFE, 0xFF) : "utf_32_be",        
                   (0xFF, 0xFE, 0x00, 0x00) : "utf_32_le",
                   (0xFE, 0xFF, None, None) : "utf_16_be", 
                   (0xFF, 0xFE, None, None) : "utf_16_le", 
                   (0xEF, 0xBB, 0xBF, None) : "utf_8",
                  }

        ## go to beginning of file and get the first 4 bytes
        oldFP = fp.tell()
        fp.seek(0)
        (byte1, byte2, byte3, byte4) = tuple(map(ord, fp.read(4)))

        ## try bom detection using 4 bytes, 3 bytes, or 2 bytes
        bomDetection = bomDict.get((byte1, byte2, byte3, byte4))
        if not bomDetection :
            bomDetection = bomDict.get((byte1, byte2, byte3, None))
            if not bomDetection :
                bomDetection = bomDict.get((byte1, byte2, None, None))
        
        ## if BOM detected, we're done :-)
        fp.seek(0) # No BOM, return to the beginning of the file
        if bomDetection :
            return bomDetection
        return None

    def consumeChar(self):
        char = self.__srcLine[self.__col]
        self.__col += 1
        return char

    def unconsumeChar(self):
        self.__col -= 1

    def getLine(self):
        return sef.__line

    def getCol(self):
        return self.__col
        
        self.__col -= 1

    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element
        
        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.

        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, parsing will
        have to begin again.
        """
        pass

if __name__ == "__main__":
    try:
        # Hard coded file name for now, this will need to be fixed later
        htmlFile = open("tests/utf-8-bom.html", "rU")
        stream = HTMLInputStream(htmlFile)

        print stream.consumeChar()
        print stream.consumeChar()
        print stream.consumeChar()
        print stream.consumeChar()

        print "unconsuming 2 characters and printing again"
        stream.unconsumeChar()
        stream.unconsumeChar()
        print stream.consumeChar()
        print stream.consumeChar()
        
        htmlFile.close()
    except IOError:
        print "The file does not exist."
