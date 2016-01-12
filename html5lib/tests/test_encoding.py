from __future__ import absolute_import, division, unicode_literals

import os
import unittest

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

from .support import get_data_files, TestData, test_dir, errorMessage
from html5lib import HTMLParser, inputstream


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

    assert encoding == stream.charEncoding[0].name, errorMessage(data, encoding, stream.charEncoding[0].name)


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
            assert encoding[0].name == "big5"
