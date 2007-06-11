import sys
import StringIO
import unittest

#RELEASE remove
import html5parser
#Run tests over all treewalkers/treebuilders pairs
#XXX - it would be nice to automate finding all treewalkers or to allow running just one

import treewalkers
import treebuilders
from filters.lint import Filter as LintFilter, LintError
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser, serializer, treewalkers, treebuilders
#from html5lib.filters.lint import Filter as LintFilter, LintError
#END RELEASE

from support import html5lib_test_files
from test_parser import parseTestcase

def PullDOMAdapter(node):
    from xml.dom import Node
    from xml.dom.pulldom import START_ELEMENT, END_ELEMENT, COMMENT, CHARACTERS

    if node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
        for childNode in node.childNodes:
            for event in PullDOMAdapter(childNode):
                yield event

    elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
        raise NotImplementedError("DOCTYPE nodes are not supported by PullDOM")

    elif node.nodeType == Node.COMMENT_NODE:
        yield COMMENT, node

    elif node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
        yield CHARACTERS, node

    elif node.nodeType == Node.ELEMENT_NODE:
        yield START_ELEMENT, node
        for childNode in node.childNodes:
            for event in PullDOMAdapter(childNode):
                yield event
        yield END_ELEMENT, node

    else:
        raise NotImplementedError("Node type not supported: " + str(node.nodeType))

treeTypes = {
"simpletree":  {"builder": treebuilders.getTreeBuilder("simpletree"),
                "walker":  treewalkers.getTreeWalker("simpletree")},
"DOM":         {"builder": treebuilders.getTreeBuilder("dom"),
                "walker":  treewalkers.getTreeWalker("dom")},
"PullDOM":     {"builder": treebuilders.getTreeBuilder("dom"),
                "adapter": PullDOMAdapter,
                "walker":  treewalkers.getTreeWalker("pulldom")},
}

#Try whatever etree implementations are available from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = \
        {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
         "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = \
            {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
             "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as ElementTree
    treeTypes['cElementTree'] = \
        {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
         "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
except ImportError:
    try:
        import cElementTree as ElementTree
        treeTypes['cElementTree'] = \
            {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
             "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
    except ImportError:
        pass

try:
    import lxml.etree as ElementTree
    treeTypes['lxml'] = \
        {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
         "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = \
        {"builder": treebuilders.getTreeBuilder("beautifulsoup"),
         "walker":  treewalkers.getTreeWalker("beautifulsoup")}
except ImportError:
    pass

try:
    from genshi.core import QName, Attrs
    from genshi.core import START, END, TEXT, COMMENT, DOCTYPE

    def GenshiAdapter(tree):
        text = None
        for token in treewalkers.getTreeWalker("simpletree")(tree):
            type = token["type"]
            if type in ("Characters", "SpaceCharacters"):
                if text is None:
                    text = token["data"]
                else:
                    text += token["data"]
            elif text is not None:
                yield TEXT, text, (None, -1, -1)
                text = None

            if type in ("StartTag", "EmptyTag"):
                yield (START,
                       (QName(token["name"]),
                        Attrs([(QName(attr),value) for attr,value in token["data"]])),
                       (None, -1, -1))
                if type == "EmptyTag":
                    type = "EndTag"

            if type == "EndTag":
                yield END, QName(token["name"]), (None, -1, -1)

            elif type == "Comment":
                yield COMMENT, token["data"], (None, -1, -1)

            elif type == "Doctype":
                yield DOCTYPE, token["name"], (None, -1, -1)

            else:
                pass # FIXME: What to do?

        if text is not None:
            yield TEXT, text, (None, -1, -1)

    treeTypes["genshi"] = \
        {"builder": treebuilders.getTreeBuilder("simpletree"),
         "adapter": GenshiAdapter,
         "walker":  treewalkers.getTreeWalker("genshi")}
except ImportError:
    pass

def concatenateCharacterTokens(tokens):
    charactersToken = None
    for token in tokens:
        type = token["type"]
        if type in ("Characters", "SpaceCharacters"):
            if charactersToken is None:
                charactersToken = {"type": "Characters", "data": token["data"]}
            else:
                charactersToken["data"] += token["data"]
        else:
            if charactersToken is not None:
                yield charactersToken
                charactersToken = None
            yield token
    if charactersToken is not None:
        yield charactersToken

def convertTokens(tokens):
    output = []
    indent = 0
    for token in concatenateCharacterTokens(tokens):
        type = token["type"]
        if type in ("StartTag", "EmptyTag"):
            output.append(u"%s<%s>" % (" "*indent, token["name"]))
            indent += 2
            attrs = token["data"]
            if attrs:
                if hasattr(attrs, "items"):
                    attrs = attrs.items()
                attrs.sort()
                for name, value in attrs:
                    output.append(u"%s%s=\"%s\"" % (" "*indent, name, value))
            if type == "EmptyTag":
                indent -= 2
        elif type == "EndTag":
            indent -= 2
        elif type == "Comment":
            output.append("%s<!-- %s -->" % (" "*indent, token["data"]))
        elif type == "Doctype":
            output.append("%s<!DOCTYPE %s>" % (" "*indent, token["name"]))
        elif type in ("Characters", "SpaceCharacters"):
            output.append("%s\"%s\"" % (" "*indent, token["data"]))
        else:
            pass # TODO: what to do with errors?
    return u"\n".join(output)

import re
attrlist = re.compile(r"^(\s+)\w+=.*(\n\1\w+=.*)+",re.M)
def sortattrs(x):
  lines = x.group(0).split("\n")
  lines.sort()
  return "\n".join(lines)

class TestCase(unittest.TestCase):
    def runTest(self, innerHTML, input, expected, errors, treeClass):
        p = html5parser.HTMLParser(tree = treeClass["builder"])

        if innerHTML:
            document = p.parseFragment(StringIO.StringIO(input), innerHTML)
        else:
            document = p.parse(StringIO.StringIO(input))
        document = treeClass.get("adapter", lambda x: x)(document)
        try:
            output = convertTokens(LintFilter(treeClass["walker"](document)))
            output = attrlist.sub(sortattrs, output)
            expected = attrlist.sub(sortattrs, expected)
            errorMsg = "\n".join(["\n\nExpected:", expected,
                                     "\nRecieved:", output])
            self.assertEquals(expected, output, errorMsg)
        except LintError, le:
            self.fail(le.message)
        except NotImplementedError:
            pass # Amnesty for those that confess...

def test_treewalker():
    sys.stdout.write('Testing tree walkers '+ " ".join(treeTypes.keys()) + "\n")

    for name, cls in treeTypes.iteritems():
        for filename in html5lib_test_files('tree-construction'):
            f = open(filename)
            tests = f.read().split("#data\n")
            for test in tests:
                if test == "":
                    continue
                test = "#data\n" + test
                innerHTML, input, expected, errors = parseTestcase(test)
                yield TestCase.runTest, innerHTML, input, expected, errors, name, cls

def buildTestSuite():
    tests = 0
    for func, innerHTML, input, expected, errors, treeName, treeCls in test_treewalker():
        tests += 1
        testName = 'test%d' % tests
        def testFunc(self, method=func, innerHTML=innerHTML, input=input,
            expected=expected, errors=errors, treeCls=treeCls):
            method(self, innerHTML, input, expected, errors, treeCls)
        testFunc.__doc__ = 'Parser %s Tree %s Input: %s'%(testName, treeName, input)
        setattr(TestCase, testName, testFunc)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
