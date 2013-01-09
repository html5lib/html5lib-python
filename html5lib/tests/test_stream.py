from __future__ import absolute_import
from . import support
import unittest, codecs

from html5lib.inputstream import HTMLInputStream, HTMLUnicodeInputStream, HTMLBinaryInputStream

class HTMLUnicodeInputStreamShortChunk(HTMLUnicodeInputStream):
    _defaultChunkSize = 2

class HTMLBinaryInputStreamShortChunk(HTMLBinaryInputStream):
    _defaultChunkSize = 2

class HTMLInputStreamTest(unittest.TestCase):

    def test_char_ascii(self):
        stream = HTMLInputStream("'", encoding=u'ascii')
        self.assertEquals(stream.charEncoding[0], u'ascii')
        self.assertEquals(stream.char(), u"'")
    test_char_ascii.func_annotations = {}

    def test_char_utf8(self):
        stream = HTMLInputStream(u'\u2018'.encode(u'utf-8'), encoding=u'utf-8')
        self.assertEquals(stream.charEncoding[0], u'utf-8')
        self.assertEquals(stream.char(), u'\u2018')
    test_char_utf8.func_annotations = {}

    def test_char_win1252(self):
        stream = HTMLInputStream(u"\xa9\xf1\u2019".encode(u'windows-1252'))
        self.assertEquals(stream.charEncoding[0], u'windows-1252')
        self.assertEquals(stream.char(), u"\xa9")
        self.assertEquals(stream.char(), u"\xf1")
        self.assertEquals(stream.char(), u"\u2019")
    test_char_win1252.func_annotations = {}

    def test_bom(self):
        stream = HTMLInputStream(codecs.BOM_UTF8 + "'")
        self.assertEquals(stream.charEncoding[0], u'utf-8')
        self.assertEquals(stream.char(), u"'")
    test_bom.func_annotations = {}

    def test_utf_16(self):
        stream = HTMLInputStream((u' '*1025).encode(u'utf-16'))
        self.assert_(stream.charEncoding[0] in [u'utf-16-le', u'utf-16-be'], stream.charEncoding)
        self.assertEquals(len(stream.charsUntil(u' ', True)), 1025)
    test_utf_16.func_annotations = {}

    def test_newlines(self):
        stream = HTMLBinaryInputStreamShortChunk(codecs.BOM_UTF8 + "a\nbb\r\nccc\rddddxe")
        self.assertEquals(stream.position(), (1, 0))
        self.assertEquals(stream.charsUntil(u'c'), u"a\nbb\n")
        self.assertEquals(stream.position(), (3, 0))
        self.assertEquals(stream.charsUntil(u'x'), u"ccc\ndddd")
        self.assertEquals(stream.position(), (4, 4))
        self.assertEquals(stream.charsUntil(u'e'), u"x")
        self.assertEquals(stream.position(), (4, 5))
    test_newlines.func_annotations = {}

    def test_newlines2(self):
        size = HTMLUnicodeInputStream._defaultChunkSize
        stream = HTMLInputStream(u"\r" * size + u"\n")
        self.assertEquals(stream.charsUntil(u'x'), u"\n" * size)
    test_newlines2.func_annotations = {}

    def test_position(self):
        stream = HTMLBinaryInputStreamShortChunk(codecs.BOM_UTF8 + "a\nbb\nccc\nddde\nf\ngh")
        self.assertEquals(stream.position(), (1, 0))
        self.assertEquals(stream.charsUntil(u'c'), u"a\nbb\n")
        self.assertEquals(stream.position(), (3, 0))
        stream.unget(u"\n")
        self.assertEquals(stream.position(), (2, 2))
        self.assertEquals(stream.charsUntil(u'c'), u"\n")
        self.assertEquals(stream.position(), (3, 0))
        stream.unget(u"\n")
        self.assertEquals(stream.position(), (2, 2))
        self.assertEquals(stream.char(), u"\n")
        self.assertEquals(stream.position(), (3, 0))
        self.assertEquals(stream.charsUntil(u'e'), u"ccc\nddd")
        self.assertEquals(stream.position(), (4, 3))
        self.assertEquals(stream.charsUntil(u'h'), u"e\nf\ng")
        self.assertEquals(stream.position(), (6, 1))
    test_position.func_annotations = {}

    def test_position2(self):
        stream = HTMLUnicodeInputStreamShortChunk(u"abc\nd")
        self.assertEquals(stream.position(), (1, 0))
        self.assertEquals(stream.char(), u"a")
        self.assertEquals(stream.position(), (1, 1))
        self.assertEquals(stream.char(), u"b")
        self.assertEquals(stream.position(), (1, 2))
        self.assertEquals(stream.char(), u"c")
        self.assertEquals(stream.position(), (1, 3))
        self.assertEquals(stream.char(), u"\n")
        self.assertEquals(stream.position(), (2, 0))
        self.assertEquals(stream.char(), u"d")
        self.assertEquals(stream.position(), (2, 1))
    test_position2.func_annotations = {}

def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
buildTestSuite.func_annotations = {}

def main():
    buildTestSuite()
    unittest.main()
main.func_annotations = {}

if __name__ == u'__main__':
    main()
