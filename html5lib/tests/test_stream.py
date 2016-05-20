from __future__ import absolute_import, division, unicode_literals

from . import support  # noqa

import codecs
from io import BytesIO

import six
from six.moves import http_client, urllib

from html5lib.inputstream import (BufferedStream, HTMLInputStream,
                                  HTMLUnicodeInputStream, HTMLBinaryInputStream)


def test_basic():
    s = b"abc"
    fp = BufferedStream(BytesIO(s))
    read = fp.read(10)
    assert read == s


def test_read_length():
    fp = BufferedStream(BytesIO(b"abcdef"))
    read1 = fp.read(1)
    assert read1 == b"a"
    read2 = fp.read(2)
    assert read2 == b"bc"
    read3 = fp.read(3)
    assert read3 == b"def"
    read4 = fp.read(4)
    assert read4 == b""


def test_tell():
    fp = BufferedStream(BytesIO(b"abcdef"))
    read1 = fp.read(1)
    assert read1 == b"a"
    assert fp.tell() == 1
    read2 = fp.read(2)
    assert read2 == b"bc"
    assert fp.tell() == 3
    read3 = fp.read(3)
    assert read3 == b"def"
    assert fp.tell() == 6
    read4 = fp.read(4)
    assert read4 == b""
    assert fp.tell() == 6


def test_seek():
    fp = BufferedStream(BytesIO(b"abcdef"))
    read1 = fp.read(1)
    assert read1 == b"a"
    fp.seek(0)
    read2 = fp.read(1)
    assert read2 == b"a"
    read3 = fp.read(2)
    assert read3 == b"bc"
    fp.seek(2)
    read4 = fp.read(2)
    assert read4 == b"cd"
    fp.seek(4)
    read5 = fp.read(2)
    assert read5 == b"ef"


def test_seek_tell():
    fp = BufferedStream(BytesIO(b"abcdef"))
    read1 = fp.read(1)
    assert read1 == b"a"
    assert fp.tell() == 1
    fp.seek(0)
    read2 = fp.read(1)
    assert read2 == b"a"
    assert fp.tell() == 1
    read3 = fp.read(2)
    assert read3 == b"bc"
    assert fp.tell() == 3
    fp.seek(2)
    read4 = fp.read(2)
    assert read4 == b"cd"
    assert fp.tell() == 4
    fp.seek(4)
    read5 = fp.read(2)
    assert read5 == b"ef"
    assert fp.tell() == 6


class HTMLUnicodeInputStreamShortChunk(HTMLUnicodeInputStream):
    _defaultChunkSize = 2


class HTMLBinaryInputStreamShortChunk(HTMLBinaryInputStream):
    _defaultChunkSize = 2


def test_char_ascii():
    stream = HTMLInputStream(b"'", encoding='ascii')
    assert stream.charEncoding[0].name == 'windows-1252'
    assert stream.char() == "'"


def test_char_utf8():
    stream = HTMLInputStream('\u2018'.encode('utf-8'), encoding='utf-8')
    assert stream.charEncoding[0].name == 'utf-8'
    assert stream.char() == '\u2018'


def test_char_win1252():
    stream = HTMLInputStream("\xa9\xf1\u2019".encode('windows-1252'))
    assert stream.charEncoding[0].name == 'windows-1252'
    assert stream.char() == "\xa9"
    assert stream.char() == "\xf1"
    assert stream.char() == "\u2019"


def test_bom():
    stream = HTMLInputStream(codecs.BOM_UTF8 + b"'")
    assert stream.charEncoding[0].name == 'utf-8'
    assert stream.char() == "'"


def test_utf_16():
    stream = HTMLInputStream((' ' * 1025).encode('utf-16'))
    assert stream.charEncoding[0].name in ['utf-16le', 'utf-16be']
    assert len(stream.charsUntil(' ', True)) == 1025


def test_newlines():
    stream = HTMLBinaryInputStreamShortChunk(codecs.BOM_UTF8 + b"a\nbb\r\nccc\rddddxe")
    assert stream.position() == (1, 0)
    assert stream.charsUntil('c') == "a\nbb\n"
    assert stream.position() == (3, 0)
    assert stream.charsUntil('x') == "ccc\ndddd"
    assert stream.position() == (4, 4)
    assert stream.charsUntil('e') == "x"
    assert stream.position() == (4, 5)


def test_newlines2():
    size = HTMLUnicodeInputStream._defaultChunkSize
    stream = HTMLInputStream("\r" * size + "\n")
    assert stream.charsUntil('x') == "\n" * size


def test_position():
    stream = HTMLBinaryInputStreamShortChunk(codecs.BOM_UTF8 + b"a\nbb\nccc\nddde\nf\ngh")
    assert stream.position() == (1, 0)
    assert stream.charsUntil('c') == "a\nbb\n"
    assert stream.position() == (3, 0)
    stream.unget("\n")
    assert stream.position() == (2, 2)
    assert stream.charsUntil('c') == "\n"
    assert stream.position() == (3, 0)
    stream.unget("\n")
    assert stream.position() == (2, 2)
    assert stream.char() == "\n"
    assert stream.position() == (3, 0)
    assert stream.charsUntil('e') == "ccc\nddd"
    assert stream.position() == (4, 3)
    assert stream.charsUntil('h') == "e\nf\ng"
    assert stream.position() == (6, 1)


def test_position2():
    stream = HTMLUnicodeInputStreamShortChunk("abc\nd")
    assert stream.position() == (1, 0)
    assert stream.char() == "a"
    assert stream.position() == (1, 1)
    assert stream.char() == "b"
    assert stream.position() == (1, 2)
    assert stream.char() == "c"
    assert stream.position() == (1, 3)
    assert stream.char() == "\n"
    assert stream.position() == (2, 0)
    assert stream.char() == "d"
    assert stream.position() == (2, 1)


def test_python_issue_20007():
    """
    Make sure we have a work-around for Python bug #20007
    http://bugs.python.org/issue20007
    """
    class FakeSocket(object):
        def makefile(self, _mode, _bufsize=None):
            return BytesIO(b"HTTP/1.1 200 Ok\r\n\r\nText")

    source = http_client.HTTPResponse(FakeSocket())
    source.begin()
    stream = HTMLInputStream(source)
    assert stream.charsUntil(" ") == "Text"


def test_python_issue_20007_b():
    """
    Make sure we have a work-around for Python bug #20007
    http://bugs.python.org/issue20007
    """
    if six.PY2:
        return

    class FakeSocket(object):
        def makefile(self, _mode, _bufsize=None):
            return BytesIO(b"HTTP/1.1 200 Ok\r\n\r\nText")

    source = http_client.HTTPResponse(FakeSocket())
    source.begin()
    wrapped = urllib.response.addinfourl(source, source.msg, "http://example.com")
    stream = HTMLInputStream(wrapped)
    assert stream.charsUntil(" ") == "Text"
