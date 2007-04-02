#!/usr/bin/env python
"""Testcases for the HTML Sanitizer"""
import unittest
import new
import itertools

import sanitizer

class TestCase(unittest.TestCase):
    def setUp(self):
        self.sanitizer = sanitizer.HTMLSanitizer()
    
    def fragmentEqual(self, input, expected):
        output = self.sanitizer.sanitize(input)
        self.assertEqual(output, expected,
                         "\nExpected:\n%s\n\nRecieved:\n%s\n"%(expected, output))

    def test_allow_colons_in_path(self):
        self.fragmentEqual("<a href=\"./this:that\">foo</a>",
                           "<a href=\"./this:that\">foo</a>")

def tags_allowed():
    for tagName in sanitizer.HTMLSanitizer.defaults['acceptable_elements']:
        yield (TestCase.fragmentEqual,
               "<%(tagName)s title='1'>foo <bad>bar</bad> baz</%(tagName)s>"%{"tagName":tagName},
               "<%(tagName)s title=\"1\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</%(tagName)s>"%{"tagName":tagName})

def attrs_allowed():
    for attrName in sanitizer.HTMLSanitizer.defaults['acceptable_attributes']:
        yield (TestCase.fragmentEqual,
               "<p %(attrName)s='foo'>foo <bad>bar</bad> baz</p>"%{"attrName":attrName},
               "<p %(attrName)s=\"foo\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</p>"%{"attrName":attrName})

def attrs_forbidden():
    for attrName in sanitizer.HTMLSanitizer.defaults['acceptable_attributes']:
        attrName=attrName+"X"
        yield (TestCase.fragmentEqual,
               "<p %(attrName)s='display: none;'>foo <bad>bar</bad> baz</p>"%{"attrName":attrName},
               "<p>foo &lt;bad>bar&lt;/bad> baz</p>")

def buildTestSuite():
    tests = 0
    for test in itertools.chain(tags_allowed(), attrs_allowed()):
        func = test[0]
        tests += 1
        testName = 'test%d' % tests
        def testFunc(self):
            func(self, *test[1:])
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    testSuite = unittest.TestLoader().loadTestsFromTestCase(TestCase)
    return testSuite

def main():
    unittest.main(defaultTest="buildTestSuite")

if __name__ == "__main__":
    main()