import codecs

class HTMLInputStream(object):
    """For reading data from an input stream

    This deals with character encoding issues automatically.

    This keeps track of the current line and column number in the file
    automatically, as you consume and unconsume characters.
    """

    def __init__(self, file, encoding = None):
        """ Initialise the HTMLInputReader.

        The file parameter must be a File object.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """

        self.__line = 1 # Current line number
        self.__col = 0  # Current column number
        self.__lineBreaks = [0]

        # Keep a reference to the unencoded file object so that a new
        # EncodedFile can be created later if the encoding is declared
        # in a meta element
        self.__file = file

        skipBOM = False
        self.__charEncoding = self.__detectBOM(file)
        if self.__charEncoding:
            # The encoding is known from the BOM, don't allow later
            # declarations from the meta element to override this.
            skipBOM = True
            self.__allowEncodingOverride = False
        else:
            # Using the default encoding, don't allow later
            # declarations from the meta element to override this.
            self.__allowEncodingOverride = True
            self.__charEncoding = "cp1252" # default to Windows-1252

        self.__encodedFile = codecs.EncodedFile(file, self.__charEncoding)
        if skipBOM:
            self.__encodedFile.read(1)

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
        char = unicode(self.__encodedFile.read(1), self.__charEncoding)
        if char == "\n":
            # Move to next line and reset column count
            self.__line += 1
            self.__col = 0
            self.__lineBreaks.append(self.__encodedFile.tell())
        else:
            # Just increment the column counter
            self.__col += 1
        return char or None

    def unconsumeChar(self):
        """Unconsume the previous character by seeking backwards thorough
        the file.
        """
        self.__encodedFile.seek(-1, 1)
        if self.__encodedFile.tell()+1 == self.__lineBreaks[-1]:
            self.__line -= 1
            self.__lineBreaks.pop()
            self.__col = self.__encodedFile.tell()-self.__lineBreaks[-1]
        else:
            self.__col -= 1

    def getLine(self):
        """Return the current line number
        """
        return self.__line

    def getCol(self):
        """Return the current column number along the current line
        """
        return self.__col

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

        char = stream.consumeChar()
        while char:
            line = stream.getLine()
            col = stream.getCol()
            if char == "\n":
                print "LF (%d, %d)" % (line, col)
            else:
                print "%s (%d, %d)" % (char, line, col)
            char = stream.consumeChar()
        print "EOF"
        htmlFile.close()
    except IOError:
        print "The file does not exist."
