import sys
import unittest
from support import simplejson, html5lib_test_files

#RELEASE remove
import html5parser
import serializer
from treewalkers._base import TreeWalker
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser, serializer
#from html5lib.treewalkers._base import TreeWalker
#END RELEASE

#Run the serialize error checks
checkSerializeErrors = False

class JsonWalker(TreeWalker):
    def __iter__(self):
        for token in self.tree:
            type = token[0]
            if type == "StartTag":
                yield self.startTag(token[1], token[2])
            elif type == "EndTag":
                yield self.endTag(token[1])
            elif type == "EmptyTag":
                for token in self.emptyTag(token[1], token[2]):
                    yield token
            elif type == "Comment":
                yield self.comment(token[1])
            elif type in ("Characters", "SpaceCharacters"):
                for token in self.text(token[1]):
                    yield token
            elif type == "Doctype":
                yield self.doctype(token[1])
            else:
                raise ValueError("Unknown token type: " + type)

class TestCase(unittest.TestCase):
    def addTest(cls, name, expected, input, description, options):
        func = lambda self: self.mockTest(expected, input, options)
        func.__doc__ = "\t".join([description, str(input), str(options)])
        setattr(cls, name, func)
    addTest = classmethod(addTest)

    def mockTest(self, expected, input, options):
        result = self.serialize_html(input, options)
        if len(expected) == 1:
            self.assertEquals(expected[0], result)
        elif result not in expected:
            self.fail("Expected: %s, Received: %s" % (expected, result))

    def serialize_html(self, input, options):
        options = dict([(str(k),v) for k,v in options.iteritems()])
        return u''.join(serializer.HTMLSerializer(**options).
                serialize(JsonWalker(input),options.get("encoding",None)))

def test_serializer():
    for filename in html5lib_test_files('serializer', '*.test'):
        tests = simplejson.load(file(filename))
        for test in tests['tests']:
            yield test

def buildTestSuite():
    tests = 0
    for test in test_serializer():
        tests += 1
        testName = 'test%d' % tests
        TestCase.addTest(testName, test["expected"], test["input"], \
            test["description"], test.get("options", {}))
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    # the following is temporary while the unit tests for parse errors are
    # still in flux
    if '-p' in sys.argv: # suppress check for serialize errors
        sys.argv.remove('-p')
        global checkSerializeErrors
        checkSerializeErrors = False
       
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
