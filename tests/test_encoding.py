import os
import unittest
from support import html5lib_test_files

#RELEASE remove
import inputstream
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import inputstream
#END RELEASE

import re, unittest, inputstream

class Html5EncodingTestCase(unittest.TestCase): pass

def buildTestSuite():
    for filename in html5lib_test_files("encoding"):
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
            data = open("../testdata/encoding/chardet/test_big5.txt").read()
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
