from __future__ import absolute_import, division, unicode_literals

import os

from .support import get_data_files, test_dir, errorMessage, TestData as _TestData
from html5lib import HTMLParser, inputstream


def test_basic_prescan_length():
    data = "<title>Caf\u00E9</title><!--a--><meta charset='utf-8'>".encode('utf-8')
    pad = 1024 - len(data) + 1
    data = data.replace(b"-a-", b"-" + (b"a" * pad) + b"-")
    assert len(data) == 1024  # Sanity
    stream = inputstream.HTMLBinaryInputStream(data, chardet=False)
    assert 'utf-8' == stream.charEncoding[0].name


def test_parser_reparse():
    data = "<title>Caf\u00E9</title><!--a--><meta charset='utf-8'>".encode('utf-8')
    pad = 10240 - len(data) + 1
    data = data.replace(b"-a-", b"-" + (b"a" * pad) + b"-")
    assert len(data) == 10240  # Sanity
    stream = inputstream.HTMLBinaryInputStream(data, chardet=False)
    assert 'windows-1252' == stream.charEncoding[0].name
    p = HTMLParser(namespaceHTMLElements=False)
    doc = p.parse(data, useChardet=False)
    assert 'utf-8' == p.documentEncoding
    assert doc.find(".//title").text == "Caf\u00E9"


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
        tests = _TestData(filename, b"data", encoding=None)
        for idx, test in enumerate(tests):
            yield (runParserEncodingTest, test[b'data'], test[b'encoding'])
            yield (runPreScanEncodingTest, test[b'data'], test[b'encoding'])

try:
    try:
        import charade  # noqa
    except ImportError:
        import chardet  # noqa
except ImportError:
    print("charade/chardet not found, skipping chardet tests")
else:
    def test_chardet():
        with open(os.path.join(test_dir, "encoding", "chardet", "test_big5.txt"), "rb") as fp:
            encoding = inputstream.HTMLInputStream(fp.read()).charEncoding
            assert encoding[0].name == "big5"
