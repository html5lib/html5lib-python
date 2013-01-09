from __future__ import absolute_import
import os
import sys
import unittest
import warnings
from itertools import izip

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

from .support import get_data_files, TestData, convertExpected

from html5lib import html5parser, treewalkers, treebuilders, constants
from html5lib.filters.lint import Filter as LintFilter, LintError

def PullDOMAdapter(node):
    from xml.dom import Node
    from xml.dom.pulldom import START_ELEMENT, END_ELEMENT, COMMENT, CHARACTERS

    if node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
        for childNode in node.childNodes:
            for event in PullDOMAdapter(childNode):
                yield event

    elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
        raise NotImplementedError(u"DOCTYPE nodes are not supported by PullDOM")

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
        raise NotImplementedError(u"Node type not supported: " + unicode(node.nodeType))
PullDOMAdapter.func_annotations = {}

treeTypes = {
u"simpletree":  {u"builder": treebuilders.getTreeBuilder(u"simpletree"),
                u"walker":  treewalkers.getTreeWalker(u"simpletree")},
u"DOM":         {u"builder": treebuilders.getTreeBuilder(u"dom"),
                u"walker":  treewalkers.getTreeWalker(u"dom")},
u"PullDOM":     {u"builder": treebuilders.getTreeBuilder(u"dom"),
                u"adapter": PullDOMAdapter,
                u"walker":  treewalkers.getTreeWalker(u"pulldom")},
}

#Try whatever etree implementations are available from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes[u'ElementTree'] = \
        {u"builder": treebuilders.getTreeBuilder(u"etree", ElementTree),
         u"walker":  treewalkers.getTreeWalker(u"etree", ElementTree)}
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes[u'ElementTree'] = \
            {u"builder": treebuilders.getTreeBuilder(u"etree", ElementTree),
             u"walker":  treewalkers.getTreeWalker(u"etree", ElementTree)}
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as ElementTree
    treeTypes[u'cElementTree'] = \
        {u"builder": treebuilders.getTreeBuilder(u"etree", ElementTree),
         u"walker":  treewalkers.getTreeWalker(u"etree", ElementTree)}
except ImportError:
    try:
        import cElementTree as ElementTree
        treeTypes[u'cElementTree'] = \
            {u"builder": treebuilders.getTreeBuilder(u"etree", ElementTree),
             u"walker":  treewalkers.getTreeWalker(u"etree", ElementTree)}
    except ImportError:
        pass

try:
    import lxml.etree as ElementTree
#    treeTypes['lxml_as_etree'] = \
#        {"builder": treebuilders.getTreeBuilder("etree", ElementTree),
#         "walker":  treewalkers.getTreeWalker("etree", ElementTree)}
    treeTypes[u'lxml_native'] = \
        {u"builder": treebuilders.getTreeBuilder(u"lxml"),
         u"walker":  treewalkers.getTreeWalker(u"lxml")}
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes[u"beautifulsoup"] = \
        {u"builder": treebuilders.getTreeBuilder(u"beautifulsoup"),
         u"walker":  treewalkers.getTreeWalker(u"beautifulsoup")}
except ImportError:
    pass
    
#Try whatever etree implementations are available from a list that are
#"supposed" to work
try:
    import pxdom
    treeTypes[u'pxdom'] = \
        {u"builder": treebuilders.getTreeBuilder(u"dom", pxdom),
         u"walker":  treewalkers.getTreeWalker(u"dom")}
except ImportError:
    pass

try:
    from genshi.core import QName, Attrs
    from genshi.core import START, END, TEXT, COMMENT, DOCTYPE

    def GenshiAdapter(tree):
        text = None
        for token in treewalkers.getTreeWalker(u"simpletree")(tree):
            type = token[u"type"]
            if type in (u"Characters", u"SpaceCharacters"):
                if text is None:
                    text = token[u"data"]
                else:
                    text += token[u"data"]
            elif text is not None:
                yield TEXT, text, (None, -1, -1)
                text = None

            if type in (u"StartTag", u"EmptyTag"):
                if token[u"namespace"]:
                    name = u"{%s}%s" % (token[u"namespace"], token[u"name"])
                else:
                    name = token[u"name"]
                yield (START,
                       (QName(name),
                        Attrs([(QName(attr),value) for attr,value in token[u"data"]])),
                       (None, -1, -1))
                if type == u"EmptyTag":
                    type = u"EndTag"

            if type == u"EndTag":
                yield END, QName(token[u"name"]), (None, -1, -1)

            elif type == u"Comment":
                yield COMMENT, token[u"data"], (None, -1, -1)

            elif type == u"Doctype":
                yield DOCTYPE, (token[u"name"], token[u"publicId"], 
                                token[u"systemId"]), (None, -1, -1)

            else:
                pass # FIXME: What to do?

        if text is not None:
            yield TEXT, text, (None, -1, -1)
    GenshiAdapter.func_annotations = {}

    #treeTypes["genshi"] = \
    #    {"builder": treebuilders.getTreeBuilder("simpletree"),
    #     "adapter": GenshiAdapter,
    #     "walker":  treewalkers.getTreeWalker("genshi")}
except ImportError:
    pass

def concatenateCharacterTokens(tokens):
    charactersToken = None
    for token in tokens:
        type = token[u"type"]
        if type in (u"Characters", u"SpaceCharacters"):
            if charactersToken is None:
                charactersToken = {u"type": u"Characters", u"data": token[u"data"]}
            else:
                charactersToken[u"data"] += token[u"data"]
        else:
            if charactersToken is not None:
                yield charactersToken
                charactersToken = None
            yield token
    if charactersToken is not None:
        yield charactersToken
concatenateCharacterTokens.func_annotations = {}

def convertTokens(tokens):
    output = []
    indent = 0
    for token in concatenateCharacterTokens(tokens):
        type = token[u"type"]
        if type in (u"StartTag", u"EmptyTag"):
            if (token[u"namespace"] and
                token[u"namespace"] != constants.namespaces[u"html"]):
                if token[u"namespace"] in constants.prefixes:
                    name = constants.prefixes[token[u"namespace"]]
                else:
                    name = token[u"namespace"]
                name += u" " + token[u"name"]
            else:
                name = token[u"name"]
            output.append(u"%s<%s>" % (u" "*indent, name))
            indent += 2
            attrs = token[u"data"]
            if attrs:
                #TODO: Remove this if statement, attrs should always exist
                for (namespace,name),value in sorted(attrs.items()):
                    if namespace:
                        if namespace in constants.prefixes:
                            outputname = constants.prefixes[namespace]
                        else:
                            outputname = namespace
                        outputname += u" " + name
                    else:
                        outputname = name
                    output.append(u"%s%s=\"%s\"" % (u" "*indent, outputname, value))
            if type == u"EmptyTag":
                indent -= 2
        elif type == u"EndTag":
            indent -= 2
        elif type == u"Comment":
            output.append(u"%s<!-- %s -->" % (u" "*indent, token[u"data"]))
        elif type == u"Doctype":
            if token[u"name"]:
                if token[u"publicId"]:
                    output.append(u"""%s<!DOCTYPE %s "%s" "%s">"""% 
                                  (u" "*indent, token[u"name"], 
                                   token[u"publicId"],
                                   token[u"systemId"] and token[u"systemId"] or u""))
                elif token[u"systemId"]:
                    output.append(u"""%s<!DOCTYPE %s "" "%s">"""% 
                                  (u" "*indent, token[u"name"], 
                                   token[u"systemId"]))
                else:
                    output.append(u"%s<!DOCTYPE %s>"%(u" "*indent,
                                                     token[u"name"]))
            else:
                output.append(u"%s<!DOCTYPE >" % (u" "*indent,))
        elif type in (u"Characters", u"SpaceCharacters"):
            output.append(u"%s\"%s\"" % (u" "*indent, token[u"data"]))
        else:
            pass # TODO: what to do with errors?
    return u"\n".join(output)
convertTokens.func_annotations = {}

import re
attrlist = re.compile(ur"^(\s+)\w+=.*(\n\1\w+=.*)+",re.M)
def sortattrs(x):
  lines = x.group(0).split(u"\n")
  lines.sort()
  return u"\n".join(lines)
sortattrs.func_annotations = {}


class TokenTestCase(unittest.TestCase):
    def test_all_tokens(self):
        expected = [
            {u'data': {}, u'type': u'StartTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'html'},
            {u'data': {}, u'type': u'StartTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'head'},
            {u'data': {}, u'type': u'EndTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'head'},
            {u'data': {}, u'type': u'StartTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'body'},
            {u'data': u'a', u'type': u'Characters'},
            {u'data': {}, u'type': u'StartTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'div'},
            {u'data': u'b', u'type': u'Characters'},
            {u'data': {}, u'type': u'EndTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'div'},
            {u'data': u'c', u'type': u'Characters'},
            {u'data': {}, u'type': u'EndTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'body'},
            {u'data': {}, u'type': u'EndTag', u'namespace': u'http://www.w3.org/1999/xhtml', u'name': u'html'}
            ]
        for treeName, treeCls in treeTypes.items():
            p = html5parser.HTMLParser(tree = treeCls[u"builder"])
            document = p.parse(u"<html><head></head><body>a<div>b</div>c</body></html>")
            document = treeCls.get(u"adapter", lambda x: x)(document)
            output = treeCls[u"walker"](document)
            for expectedToken, outputToken in izip(expected, output):
                self.assertEqual(expectedToken, outputToken)
    test_all_tokens.func_annotations = {}

def runTreewalkerTest(innerHTML, input, expected, errors, treeClass):
    warnings.resetwarnings()
    warnings.simplefilter(u"error")
    try:
        p = html5parser.HTMLParser(tree = treeClass[u"builder"])
        if innerHTML:
            document = p.parseFragment(input, innerHTML)
        else:
            document = p.parse(input)
    except constants.DataLossWarning:
        #Ignore testcases we know we don't pass
        return

    document = treeClass.get(u"adapter", lambda x: x)(document)
    try:
        output = convertTokens(treeClass[u"walker"](document))
        output = attrlist.sub(sortattrs, output)
        expected = attrlist.sub(sortattrs, convertExpected(expected))
        assert expected == output, u"\n".join([
                u"", u"Input:", input,
                u"", u"Expected:", expected,
                u"", u"Received:", output
                ])
    except NotImplementedError:
        pass # Amnesty for those that confess...
runTreewalkerTest.func_annotations = {}
            
def test_treewalker():
    sys.stdout.write(u'Testing tree walkers '+ u" ".join(list(treeTypes.keys())) + u"\n")

    for treeName, treeCls in treeTypes.items():
        files = get_data_files(u'tree-construction')
        for filename in files:
            testName = os.path.basename(filename).replace(u".dat",u"")
            if testName == u"main-element":
                continue

            tests = TestData(filename, u"data")

            for index, test in enumerate(tests):
                (input, errors,
                 innerHTML, expected) = [test[key] for key in (u"data", u"errors",
                                                               u"document-fragment",
                                                               u"document")]
                errors = errors.split(u"\n")
                yield runTreewalkerTest, innerHTML, input, expected, errors, treeCls
test_treewalker.func_annotations = {}


