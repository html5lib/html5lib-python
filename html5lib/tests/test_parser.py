import os
import sys
import traceback
import io
import warnings
import re

warnings.simplefilter("error")

from .support import get_data_files
from .support import TestData, convert, convertExpected, treeTypes
import html5lib
from html5lib import html5parser, treebuilders, constants

#Run the parse error checks
checkParseErrors = False

#XXX - There should just be one function here but for some reason the testcase
#format differs from the treedump format by a single space character
def convertTreeDump(data):
    return "\n".join(convert(3)(data).split("\n")[1:])

namespaceExpected = re.compile(r"^(\s*)<(\S+)>", re.M).sub


def runParserTest(innerHTML, input, expected, errors, treeClass,
                  namespaceHTMLElements):
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
        errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                               "\nTraceback:", traceback.format_exc().decode('utf8')])
        assert False, errorMsg

    output = convertTreeDump(p.tree.testSerializer(document))

    expected = convertExpected(expected)
    if namespaceHTMLElements:
        expected = namespaceExpected(r"\1<html \2>", expected)

    errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                           "\nReceived:", output])
    assert expected == output, errorMsg
    errStr = ["Line: %i Col: %i %s"%(line, col, 
                                      constants.E[errorcode] % datavars if isinstance(datavars, dict) else (datavars,)) for
              ((line,col), errorcode, datavars) in p.errors]

    errorMsg2 = "\n".join(["\n\nInput:", input,
                            "\nExpected errors (" + str(len(errors)) + "):\n" + "\n".join(errors),
                            "\nActual errors (" + str(len(p.errors)) + "):\n" + "\n".join(errStr)])
    if checkParseErrors:
            assert len(p.errors) == len(errors), errorMsg2

def test_parser():
    sys.stderr.write('Testing tree builders '+ " ".join(list(treeTypes.keys())) + "\n")
    files = get_data_files('tree-construction')
    
    for filename in files:
        testName = os.path.basename(filename).replace(".dat","")

        tests = TestData(filename, "data")
        
        for index, test in enumerate(tests):
            input, errors, innerHTML, expected = [test[key] for key in
                                                      ('data', 'errors',
                                                      'document-fragment',
                                                      'document')]
            if errors:
                errors = errors.split("\n")

            for treeName, treeCls in treeTypes.items():
                for namespaceHTMLElements in (True, False):
                    print(input)
                    yield (runParserTest, innerHTML, input, expected, errors, treeCls,
                           namespaceHTMLElements)
