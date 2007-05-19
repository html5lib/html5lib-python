import sys
import os
import glob
import unittest

def buildTestSuite():
    suite = unittest.TestSuite()
    for testcase in glob.glob('test_*.py'):
        module = os.path.splitext(testcase)[0]
        suite.addTest(__import__(module).buildTestSuite())
    return suite

def main():
    # the following is temporary while the unit tests for parse errors are
    # still in flux
    if '-p' in sys.argv: # suppress check for parse errors
        import test_parser
        test_parser.checkParseErrors = False

    results = unittest.TextTestRunner().run(buildTestSuite())
    if not results.wasSuccessful(): sys.exit(1)

if __name__ == "__main__":
    #Allow us to import the parent module
#RELEASE remove
    sys.path.insert(0,os.path.abspath(os.path.join(__file__,'../../src')))
#END RELEASE
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.pardir))

    main()
