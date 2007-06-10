import sys
import os
import glob
import unittest

#RELEASE remove
if __name__ == '__main__':
    # XXX Allow us to import the sibling module
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import inputstream
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import inputstream
#END RELEASE

import re, glob, unittest, inputstream

class Html5EncodingTestCase(unittest.TestCase): pass

def buildTestSuite():
    for filename in glob.glob("encoding/*.dat"):
        test_name = os.path.basename(filename).replace('.dat',''). \
            replace('-','')
        for idx,(data,encoding) in enumerate(re.compile(
                "^#data\s*\n(.*?)\n#encoding\s*\n(.*?)\n",
                re.DOTALL|re.MULTILINE).findall(open(filename).read())):
            def encodingTest(self, data=data, encoding=encoding):
                stream = inputstream.HTMLInputStream(data,chardet=False)
                self.assertEquals(encoding.lower(), stream.charEncoding)
            setattr(Html5EncodingTestCase, 'test_%s_%d' % (test_name, idx+1),
                encodingTest)

    try:
        import chardet
        def test_chardet(self):
            data = open("encoding/chardet/test_big5.txt").read()
            encoding = inputstream.HTMLInputStream(data).charEncoding
            assert encoding.lower() == "big5"
        setattr(Html5EncodingTestCase, 'test_chardet', test_chardet)
    except ImportError:
        print "chardet not found, skipping chardet tests"

    return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
