import os
import unittest
from support import simplejson, html5lib_test_files

from html5lib import html5parser, serializer, constants
from html5lib.treewalkers._base import TreeWalker

default_namespace = constants.namespaces["html"]

class JsonWalker(TreeWalker):
    def __iter__(self):
        for token in self.tree:
            type = token[0]
            if type == "StartTag":
                if len(token) == 4:
                    namespace, name, attrib = token[1:4]
                else:
                    namespace = default_namespace
                    name, attrib = token[1:3]
                yield self.startTag(namespace, name, attrib)
            elif type == "EndTag":
                if len(token) == 3:
                    namespace, name = token[1:3]
                else:
                    namespace = default_namespace
                    name = token[1]
                yield self.endTag(namespace, name)
            elif type == "EmptyTag":
                if len(token) == 4:
                    namespace, name, attrib = token[1:]
                else:
                    namespace = default_namespace
                    name, attrib = token[1:]
                for token in self.emptyTag(namespace, name, attrib):
                    yield token
            elif type == "Comment":
                yield self.comment(token[1])
            elif type in ("Characters", "SpaceCharacters"):
                for token in self.text(token[1]):
                    yield token
            elif type == "Doctype":
                if len(token) == 4:
                    yield self.doctype(token[1], token[2], token[3])
                elif len(token) == 3:
                    yield self.doctype(token[1], token[2])
                else:
                    yield self.doctype(token[1])
            else:
                raise ValueError("Unknown token type: " + type)

class TestCase(unittest.TestCase):
    def addTest(cls, name, description, input, expected, xhtml, options):
        func = lambda self: self.mockTest(input, options, expected, xhtml)
        func.__doc__ = "\t".join([name, description, str(input), str(options)])
        setattr(cls, name, func)
    addTest = classmethod(addTest)

    def mockTest(self, input, options, expected, xhtml):
        result = self.serialize_html(input, options)
        if len(expected) == 1:
            self.assertEquals(expected[0], result, "Expected:\n%s\nActual:\n%s\nOptions\nxhtml:False\n%s"%(expected[0], result, str(options)))
        elif result not in expected:
            self.fail("Expected: %s, Received: %s" % (expected, result))

        if not xhtml: return

        result = self.serialize_xhtml(input, options)
        if len(xhtml) == 1:
            self.assertEquals(xhtml[0], result, "Expected:\n%s\nActual:\n%s\nOptions\nxhtml:True\n%s"%(xhtml[0], result, str(options)))
        elif result not in xhtml:
            self.fail("Expected: %s, Received: %s" % (xhtml, result))

    def serialize_html(self, input, options):
        options = dict([(str(k),v) for k,v in options.iteritems()])
        return u''.join(serializer.HTMLSerializer(**options).
                serialize(JsonWalker(input),options.get("encoding",None)))

    def serialize_xhtml(self, input, options):
        options = dict([(str(k),v) for k,v in options.iteritems()])
        return u''.join(serializer.XHTMLSerializer(**options).
                serialize(JsonWalker(input),options.get("encoding",None)))

def buildTestSuite():
    for filename in html5lib_test_files('serializer', '*.test'):
        test_name = os.path.basename(filename).replace('.test','')
        tests = simplejson.load(file(filename))
        for index, test in enumerate(tests['tests']):
            xhtml = test.get("xhtml", test["expected"])
            if test_name == 'optionaltags': xhtml = None
            TestCase.addTest('test_%s_%d' % (test_name, index+1),
                test["description"], test["input"], test["expected"], xhtml,
                test.get("options", {}))
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
