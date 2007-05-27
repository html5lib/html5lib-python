import sys
import os
import glob
import StringIO
import unittest
import new

try:
    import simplejson
except:
    import re
    class simplejson:
        def load(f):
            true, false = True, False
            input=re.sub(r'(".*?(?<!\\)")',r'u\1',f.read().decode('utf-8'))
            return eval(input)
        load = staticmethod(load)

#RELEASE remove
# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
import serializer
import treewalkers
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser, serializer, treewalkers
#END RELEASE

#Run the serialize error checks
checkSerializeErrors = False

class TestCase(unittest.TestCase, treewalkers._base.TreeWalker):
    def addTest(cls, name, expected, input, description, options):
        func = lambda self: self.mockTest(expected, input, options)
        func.__doc__ = "\t".join([description, str(input), str(options)])
        setattr(cls, name, new.instancemethod(func, None, cls))
    addTest = classmethod(addTest)

    def mockTest(self, expected, input, options):
        exception = None
        result = self.serialize_html(input, options)
        for alternative in expected:
            try:
                self.assertEquals(alternative, result)
            except AssertionError, ex:
                exception = ex
            else:
                break
        else:
            if exception is not None:
                raise exception

    def serialize_html(self, input, options):
        return u''.join(serializer.HTMLSerializer( \
            **dict([(str(k),v) for k,v in options.iteritems()])).
                serialize(self.normalizeTokens(input)))

    def normalizeTokens(self, tokens):
        for token in tokens:
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

def test_serializer():
    for filename in glob.glob('serializer/*.test'):
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
