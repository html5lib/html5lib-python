from __future__ import absolute_import
import os
import sys
import traceback
import io
import warnings
import re

warnings.simplefilter(u"error")

from .support import get_data_files
from .support import TestData, convert, convertExpected, treeTypes
import html5lib
from html5lib import html5parser, treebuilders, constants

#Run the parse error checks
checkParseErrors = False

#XXX - There should just be one function here but for some reason the testcase
#format differs from the treedump format by a single space character
def convertTreeDump(data):
    return u"\n".join(convert(3)(data).split(u"\n")[1:])
convertTreeDump.func_annotations = {}

namespaceExpected = re.compile(ur"^(\s*)<(\S+)>", re.M).sub


def runParserTest(innerHTML, input, expected, errors, treeClass,
                  namespaceHTMLElements):
    warnings.resetwarnings()
    warnings.simplefilter(u"error")
    #XXX - move this out into the setup function
    #concatenate all consecutive character tokens into a single token
    try:
        p = html5parser.HTMLParser(tree = treeClass,
                                   namespaceHTMLElements=namespaceHTMLElements)
    except constants.DataLossWarning:
        return

    try:
        if innerHTML:
            document = p.parseFragment(input, innerHTML)
        else:
            try:
                document = p.parse(input)
            except constants.DataLossWarning:
                return
    except:
        errorMsg = u"\n".join([u"\n\nInput:", input, u"\nExpected:", expected,
                               u"\nTraceback:", traceback.format_exc()])
        assert False, errorMsg

    output = convertTreeDump(p.tree.testSerializer(document))

    expected = convertExpected(expected)
    if namespaceHTMLElements:
        expected = namespaceExpected(ur"\1<html \2>", expected)

    errorMsg = u"\n".join([u"\n\nInput:", input, u"\nExpected:", expected,
                           u"\nReceived:", output])
    assert expected == output, errorMsg
    errStr = [u"Line: %i Col: %i %s"%(line, col, 
                                      constants.E[errorcode] % datavars if isinstance(datavars, dict) else (datavars,)) for
              ((line,col), errorcode, datavars) in p.errors]

    errorMsg2 = u"\n".join([u"\n\nInput:", input,
                            u"\nExpected errors (" + unicode(len(errors)) + u"):\n" + u"\n".join(errors),
                            u"\nActual errors (" + unicode(len(p.errors)) + u"):\n" + u"\n".join(errStr)])
    if checkParseErrors:
            assert len(p.errors) == len(errors), errorMsg2
runParserTest.func_annotations = {}

def test_parser():
    sys.stderr.write(u'Testing tree builders '+ u" ".join(list(treeTypes.keys())) + u"\n")
    files = get_data_files(u'tree-construction')
    
    for filename in files:
        testName = os.path.basename(filename).replace(u".dat",u"")
        if testName == u"main-element":
            continue

        tests = TestData(filename, u"data")
        
        for index, test in enumerate(tests):
            input, errors, innerHTML, expected = [test[key] for key in
                                                      (u'data', u'errors',
                                                      u'document-fragment',
                                                      u'document')]
            if errors:
                errors = errors.split(u"\n")

            for treeName, treeCls in treeTypes.items():
                for namespaceHTMLElements in (True, False):
                    yield (runParserTest, innerHTML, input, expected, errors, treeCls,
                           namespaceHTMLElements)
test_parser.func_annotations = {}
