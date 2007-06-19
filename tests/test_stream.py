import unittest, codecs

#RELEASE remove
if __name__ == '__main__':
  import os, sys
  os.chdir(os.path.split(os.path.abspath(__file__))[0])
  sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

from inputstream import HTMLInputStream
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib.inputstream import HTMLInputStream
#END RELEASE

class HTMLInputStreamTest(unittest.TestCase):

    def test_char_ascii(self):
        stream = HTMLInputStream("'", encoding='ascii')
        self.assertEquals(stream.charEncoding, 'ascii')
        self.assertEquals(stream.char(), "'")

    def test_char_null(self):
        stream = HTMLInputStream("\x00")
        self.assertEquals(stream.char(), u'\ufffd')

    def test_char_utf8(self):
        stream = HTMLInputStream(u'\u2018'.encode('utf-8'), encoding='utf-8')
        self.assertEquals(stream.charEncoding, 'utf-8')
        self.assertEquals(stream.char(), u'\u2018')

    def test_char_win1252(self):
        stream = HTMLInputStream(u"\xa9\xf1\u2019".encode('windows-1252'))
        self.assertEquals(stream.charEncoding, 'windows-1252')
        self.assertEquals(stream.char(), u"\xa9")
        self.assertEquals(stream.char(), u"\xf1")
        self.assertEquals(stream.char(), u"\u2019")

    def test_bom(self):
        stream = HTMLInputStream(codecs.BOM_UTF8 + "'")
        self.assertEquals(stream.charEncoding, 'utf-8')
        self.assertEquals(stream.char(), "'")

    def test_utf_16(self):
        stream = HTMLInputStream((' '*1025).encode('utf-16'))
        self.assert_(stream.charEncoding in ['utf-16-le','utf-16-be'])
        self.assertEquals(len(stream.charsUntil(' ',True)),1025)

    def test_newlines(self):
        stream = HTMLInputStream(codecs.BOM_UTF8 + "a\nbb\r\nccc\rdddd")
        self.assertEquals(stream.position(), (1, 0))
        self.assertEquals(stream.charsUntil('c'),u"a\nbb\n")
        self.assertEquals(stream.position(), (3,0))
        self.assertEquals(stream.charsUntil('x'),u"ccc\ndddd")
        self.assertEquals(stream.position(), (4,4))
        self.assertEquals(stream.lineLengths, [1,2,3])

def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == '__main__':
    main()
