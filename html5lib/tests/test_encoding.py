from __future__ import absolute_import
import re
import os
import unittest
from io import open

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

from .support import get_data_files, TestData, test_dir, errorMessage
from html5lib import HTMLParser, inputstream

class Html5EncodingTestCase(unittest.TestCase):
    def test_codec_name_a(self):
        self.assertEqual(inputstream.codecName(u"utf-8"), u"utf-8")
    test_codec_name_a.func_annotations = {}

    def test_codec_name_b(self):
        self.assertEqual(inputstream.codecName(u"utf8"), u"utf-8")
    test_codec_name_b.func_annotations = {}

    def test_codec_name_c(self):
        self.assertEqual(inputstream.codecName(u"  utf8  "), u"utf-8")
    test_codec_name_c.func_annotations = {}

    def test_codec_name_d(self):
        self.assertEqual(inputstream.codecName(u"ISO_8859--1"), u"windows-1252")
    test_codec_name_d.func_annotations = {}

def runParserEncodingTest(data, encoding):
    p = HTMLParser()
    t = p.parse(data, useChardet=False)
    encoding = encoding.lower().decode(u"ascii")

    assert encoding == p.tokenizer.stream.charEncoding[0], errorMessage(data, encoding, p.tokenizer.stream.charEncoding[0])
runParserEncodingTest.func_annotations = {}

def runPreScanEncodingTest(data, encoding):
    stream = inputstream.HTMLBinaryInputStream(data, chardet=False)
    encoding = encoding.lower().decode(u"ascii")

    # Very crude way to ignore irrelevant tests
    if len(data) > stream.numBytesMeta:
        return

    assert encoding == stream.charEncoding[0], errorMessage(data, encoding, stream.charEncoding[0])
runPreScanEncodingTest.func_annotations = {}

def test_encoding():
    for filename in get_data_files(u"encoding"):
        test_name = os.path.basename(filename).replace(u'.dat',u''). \
            replace(u'-',u'')
        tests = TestData(filename, "data", encoding=None)
        for idx, test in enumerate(tests):
            yield (runParserEncodingTest, test['data'], test['encoding'])
            yield (runPreScanEncodingTest, test['data'], test['encoding'])
test_encoding.func_annotations = {}

try:
    import chardet
    def test_chardet(self):
        data = open(os.path.join(test_dir, u"encoding" , u"chardet", u"test_big5.txt")).read()
        encoding = inputstream.HTMLInputStream(data).charEncoding
        assert encoding[0].lower() == u"big5"
    test_chardet.func_annotations = {}
    setattr(Html5EncodingTestCase, u'test_chardet', test_chardet)
except ImportError:
    print u"chardet not found, skipping chardet tests"
