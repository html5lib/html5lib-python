from __future__ import absolute_import
import unittest

from html5lib.filters.whitespace import Filter
from html5lib.constants import spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

class TestCase(unittest.TestCase):
    def runTest(self, input, expected):
        output = list(Filter(input))
        errorMsg = u"\n".join([u"\n\nInput:", unicode(input),
                              u"\nExpected:", unicode(expected),
                              u"\nReceived:", unicode(output)])
        self.assertEqual(output, expected, errorMsg)
    runTest.func_annotations = {}

    def runTestUnmodifiedOutput(self, input):
        self.runTest(input, input)
    runTestUnmodifiedOutput.func_annotations = {}

    def testPhrasingElements(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"Characters", u"data": u"This is a " },
             {u"type": u"StartTag", u"name": u"span", u"data": [] },
             {u"type": u"Characters", u"data": u"phrase" },
             {u"type": u"EndTag", u"name": u"span", u"data": []},
             {u"type": u"SpaceCharacters", u"data": u" " },
             {u"type": u"Characters", u"data": u"with" },
             {u"type": u"SpaceCharacters", u"data": u" " },
             {u"type": u"StartTag", u"name": u"em", u"data": [] },
             {u"type": u"Characters", u"data": u"emphasised text" },
             {u"type": u"EndTag", u"name": u"em", u"data": []},
             {u"type": u"Characters", u"data": u" and an " },
             {u"type": u"StartTag", u"name": u"img", u"data": [[u"alt", u"image"]] },
             {u"type": u"Characters", u"data": u"." }])
    testPhrasingElements.func_annotations = {}

    def testLeadingWhitespace(self):
        self.runTest(
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"SpaceCharacters", u"data": spaceCharacters},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}],
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"SpaceCharacters", u"data": u" "},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}])
    testLeadingWhitespace.func_annotations = {}

    def testLeadingWhitespaceAsCharacters(self):
        self.runTest(
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": spaceCharacters + u"foo"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}],
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u" foo"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}])
    testLeadingWhitespaceAsCharacters.func_annotations = {}

    def testTrailingWhitespace(self):
        self.runTest(
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"SpaceCharacters", u"data": spaceCharacters},
             {u"type": u"EndTag", u"name": u"p", u"data": []}],
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"SpaceCharacters", u"data": u" "},
             {u"type": u"EndTag", u"name": u"p", u"data": []}])
    testTrailingWhitespace.func_annotations = {}

    def testTrailingWhitespaceAsCharacters(self):
        self.runTest(
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo" + spaceCharacters},
             {u"type": u"EndTag", u"name": u"p", u"data": []}],
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo "},
             {u"type": u"EndTag", u"name": u"p", u"data": []}])
    testTrailingWhitespaceAsCharacters.func_annotations = {}

    def testWhitespace(self):
        self.runTest(
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo" + spaceCharacters + u"bar"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}],
            [{u"type": u"StartTag", u"name": u"p", u"data": []},
             {u"type": u"Characters", u"data": u"foo bar"},
             {u"type": u"EndTag", u"name": u"p", u"data": []}])
    testWhitespace.func_annotations = {}

    def testLeadingWhitespaceInPre(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"StartTag", u"name": u"pre", u"data": []},
             {u"type": u"SpaceCharacters", u"data": spaceCharacters},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"EndTag", u"name": u"pre", u"data": []}])
    testLeadingWhitespaceInPre.func_annotations = {}

    def testLeadingWhitespaceAsCharactersInPre(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"StartTag", u"name": u"pre", u"data": []},
             {u"type": u"Characters", u"data": spaceCharacters + u"foo"},
             {u"type": u"EndTag", u"name": u"pre", u"data": []}])
    testLeadingWhitespaceAsCharactersInPre.func_annotations = {}

    def testTrailingWhitespaceInPre(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"StartTag", u"name": u"pre", u"data": []},
             {u"type": u"Characters", u"data": u"foo"},
             {u"type": u"SpaceCharacters", u"data": spaceCharacters},
             {u"type": u"EndTag", u"name": u"pre", u"data": []}])
    testTrailingWhitespaceInPre.func_annotations = {}

    def testTrailingWhitespaceAsCharactersInPre(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"StartTag", u"name": u"pre", u"data": []},
             {u"type": u"Characters", u"data": u"foo" + spaceCharacters},
             {u"type": u"EndTag", u"name": u"pre", u"data": []}])
    testTrailingWhitespaceAsCharactersInPre.func_annotations = {}

    def testWhitespaceInPre(self):
        self.runTestUnmodifiedOutput(
            [{u"type": u"StartTag", u"name": u"pre", u"data": []},
             {u"type": u"Characters", u"data": u"foo" + spaceCharacters + u"bar"},
             {u"type": u"EndTag", u"name": u"pre", u"data": []}])
    testWhitespaceInPre.func_annotations = {}

def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
buildTestSuite.func_annotations = {}

def main():
    buildTestSuite()
    unittest.main()
main.func_annotations = {}

if __name__ == u"__main__":
    main()
