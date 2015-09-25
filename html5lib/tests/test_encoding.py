# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, division, unicode_literals

import os
import unittest

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

from .support import get_data_files, TestData, test_dir, errorMessage
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
    assert p.documentEncoding is None
    p.parse(data, useChardet=False)
    encoding = encoding.lower().decode("ascii")

    assert encoding == p.documentEncoding, errorMessage(data, encoding, p.documentEncoding)


def runPreScanEncodingTest(data, encoding):
    stream = inputstream.HTMLBinaryInputStream(data, chardet=False)
    encoding = encoding.lower().decode("ascii")

    # Very crude way to ignore irrelevant tests
    if len(data) > stream.numBytesMeta:
        return

    assert encoding == stream.charEncoding[0], errorMessage(data, encoding, stream.charEncoding[0])


def test_encoding():
    for filename in get_data_files("encoding"):
        tests = TestData(filename, b"data", encoding=None)
        for idx, test in enumerate(tests):
            yield (runParserEncodingTest, test[b'data'], test[b'encoding'])
            yield (runPreScanEncodingTest, test[b'data'], test[b'encoding'])

try:
    try:
        import charade  # flake8: noqa
    except ImportError:
        import chardet  # flake8: noqa
except ImportError:
    print("charade/chardet not found, skipping chardet tests")
else:
    def test_chardet():
        with open(os.path.join(test_dir, "encoding" , "chardet", "test_big5.txt"), "rb") as fp:
            encoding = inputstream.HTMLInputStream(fp.read()).charEncoding
            assert encoding[0].lower() == "big5"
