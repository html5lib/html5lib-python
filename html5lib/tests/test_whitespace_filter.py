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

from html5lib.filters.whitespace import Filter
from html5lib.constants import spaceCharacters
spaceCharacters = "".join(spaceCharacters)


def runTest(input, expected):
    output = list(Filter(input))
    errorMsg = "\n".join(["\n\nInput:", str(input),
                          "\nExpected:", str(expected),
                          "\nReceived:", str(output)])
    assert expected == output, errorMsg


def runTestUnmodifiedOutput(input):
    runTest(input, input)


def testPhrasingElements():
    runTestUnmodifiedOutput(
        [{"type": "Characters", "data": "This is a "},
         {"type": "StartTag", "name": "span", "data": []},
         {"type": "Characters", "data": "phrase"},
         {"type": "EndTag", "name": "span", "data": []},
         {"type": "SpaceCharacters", "data": " "},
         {"type": "Characters", "data": "with"},
         {"type": "SpaceCharacters", "data": " "},
         {"type": "StartTag", "name": "em", "data": []},
         {"type": "Characters", "data": "emphasised text"},
         {"type": "EndTag", "name": "em", "data": []},
         {"type": "Characters", "data": " and an "},
         {"type": "StartTag", "name": "img", "data": [["alt", "image"]]},
         {"type": "Characters", "data": "."}])


def testLeadingWhitespace():
    runTest(
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "SpaceCharacters", "data": spaceCharacters},
         {"type": "Characters", "data": "foo"},
         {"type": "EndTag", "name": "p", "data": []}],
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "SpaceCharacters", "data": " "},
         {"type": "Characters", "data": "foo"},
         {"type": "EndTag", "name": "p", "data": []}])


def testLeadingWhitespaceAsCharacters():
    runTest(
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": spaceCharacters + "foo"},
         {"type": "EndTag", "name": "p", "data": []}],
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": " foo"},
         {"type": "EndTag", "name": "p", "data": []}])


def testTrailingWhitespace():
    runTest(
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo"},
         {"type": "SpaceCharacters", "data": spaceCharacters},
         {"type": "EndTag", "name": "p", "data": []}],
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo"},
         {"type": "SpaceCharacters", "data": " "},
         {"type": "EndTag", "name": "p", "data": []}])


def testTrailingWhitespaceAsCharacters():
    runTest(
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo" + spaceCharacters},
         {"type": "EndTag", "name": "p", "data": []}],
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo "},
         {"type": "EndTag", "name": "p", "data": []}])


def testWhitespace():
    runTest(
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo" + spaceCharacters + "bar"},
         {"type": "EndTag", "name": "p", "data": []}],
        [{"type": "StartTag", "name": "p", "data": []},
         {"type": "Characters", "data": "foo bar"},
         {"type": "EndTag", "name": "p", "data": []}])


def testLeadingWhitespaceInPre():
    runTestUnmodifiedOutput(
        [{"type": "StartTag", "name": "pre", "data": []},
         {"type": "SpaceCharacters", "data": spaceCharacters},
         {"type": "Characters", "data": "foo"},
         {"type": "EndTag", "name": "pre", "data": []}])


def testLeadingWhitespaceAsCharactersInPre():
    runTestUnmodifiedOutput(
        [{"type": "StartTag", "name": "pre", "data": []},
         {"type": "Characters", "data": spaceCharacters + "foo"},
         {"type": "EndTag", "name": "pre", "data": []}])


def testTrailingWhitespaceInPre():
    runTestUnmodifiedOutput(
        [{"type": "StartTag", "name": "pre", "data": []},
         {"type": "Characters", "data": "foo"},
         {"type": "SpaceCharacters", "data": spaceCharacters},
         {"type": "EndTag", "name": "pre", "data": []}])


def testTrailingWhitespaceAsCharactersInPre():
    runTestUnmodifiedOutput(
        [{"type": "StartTag", "name": "pre", "data": []},
         {"type": "Characters", "data": "foo" + spaceCharacters},
         {"type": "EndTag", "name": "pre", "data": []}])


def testWhitespaceInPre():
    runTestUnmodifiedOutput(
        [{"type": "StartTag", "name": "pre", "data": []},
         {"type": "Characters", "data": "foo" + spaceCharacters + "bar"},
         {"type": "EndTag", "name": "pre", "data": []}])
