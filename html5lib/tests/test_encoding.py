import re
import os
import unittest

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

from .support import get_data_files, TestData, test_dir
from html5lib import HTMLParser, inputstream

class Html5EncodingTestCase(unittest.TestCase):
    def test_codec_name_a(self):
        self.assertEqual(inputstream.codecName("utf-8"), "utf-8")

    def test_codec_name_b(self):
        self.assertEqual(inputstream.codecName("utf8"), "utf-8")

    def test_codec_name_c(self):
        self.assertEqual(inputstream.codecName("  utf8  "), "utf-8")

    def test_codec_name_d(self):
        self.assertEqual(inputstream.codecName("ISO_8859--1"), "windows-1252")

def runParserEncodingTest(data, encoding):
    p = HTMLParser()
    t = p.parse(data, useChardet=False)
    encoding = encoding.lower().decode("ascii")

    errorMessage = ("Input:\n%s\nExpected:\n%s\nRecieved\n%s\n"%
                    (data, repr(encoding), 
                     repr(p.tokenizer.stream.charEncoding[0])))
    assert encoding == p.tokenizer.stream.charEncoding[0], errorMessage


def runPreScanEncodingTest(data, encoding):
    stream = inputstream.HTMLBinaryInputStream(data, chardet=False)
    encoding = encoding.lower().decode("ascii")

    if len(data) > stream.numBytesMeta:
        return

    errorMessage = ("Input:\n%s\nExpected:\n%s\nRecieved\n%s\n"%
                    (data, repr(encoding), 
                     repr(stream.charEncoding[0])))
    assert encoding == stream.charEncoding[0], errorMessage

def test_encoding():
    for filename in get_data_files("encoding"):
        test_name = os.path.basename(filename).replace('.dat',''). \
            replace('-','')
        tests = TestData(filename, b"data", encoding=None)
        for idx, test in enumerate(tests):
            yield (runParserEncodingTest, test[b'data'], test[b'encoding'])
            yield (runPreScanEncodingTest, test[b'data'], test[b'encoding'])

try:
    import chardet
    def test_chardet(self):
        data = open(os.path.join(test_dir, "encoding" , "chardet", "test_big5.txt")).read()
        encoding = inputstream.HTMLInputStream(data).charEncoding
        assert encoding[0].lower() == "big5"
    setattr(Html5EncodingTestCase, 'test_chardet', test_chardet)
except ImportError:
    print("chardet not found, skipping chardet tests")
