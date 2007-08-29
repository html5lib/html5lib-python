import os, unittest
from support import simplejson, html5lib_test_files
from html5lib.html5parser import HTMLParser
from html5lib.filters.validator import HTMLConformanceChecker

class TestCase(unittest.TestCase):
    def runValidatorTest(self, test):
        p = HTMLParser(tokenizer=HTMLConformanceChecker)
        p.parse(test['input'])
        errorCodes = [errorcode for position, errorcode, datavars in p.errors]
        if test.has_key('fail-if'):
            self.failIf(test['fail-if'] in errorCodes)
        if test.has_key('fail-unless'):
            self.failUnless(test['fail-unless'] in errorCodes)

def buildTestSuite():
    for filename in html5lib_test_files('validator', '*.test'):
        tests = simplejson.load(file(filename))
        testName = os.path.basename(filename).replace(".test","")
        for index,test in enumerate(tests['tests']):
            def testFunc(self, test=test):
                self.runValidatorTest(test)
            testFunc.__doc__ = "\t".join([testName, test['description']])
            setattr(TestCase, 'test_%s_%d' % (testName, index), testFunc)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
