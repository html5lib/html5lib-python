"""HTML 5 conformance checker

Warning: this module is experimental, incomplete, and subject to removal at any time.

Usage:
>>> from html5lib.html5parser import HTMLParser
>>> from html5lib.filters.validator import HTMLConformanceChecker
>>> p = HTMLParser(tokenizer=HTMLConformanceChecker)
>>> p.parse('<!doctype html>\n<html foo=bar></html>')
<<class 'html5lib.treebuilders.simpletree.Document'> None>
>>> p.errors
[((2, 14), 'unrecognized-attribute', {'attributeName': u'foo', 'tagName': u'html'})]
"""

import _base
from html5lib.constants import E
from html5lib import tokenizer
import gettext
_ = gettext.gettext

E.update({
    "unrecognized-attribute":
        _(u"Unrecognized attribute '%(attributeName)s' in <%(tagName)s>"),
})

globalAttributes = ['id', 'title', 'lang', 'dir', 'class', 'irrelevant']
allowedAttributeMap = {
    'html': globalAttributes + ['xmlns']
}

class HTMLConformanceChecker(_base.Filter):
    def __init__(self, stream, encoding, parseMeta, **kwargs):
        _base.Filter.__init__(self, tokenizer.HTMLTokenizer(
            stream, encoding, parseMeta, **kwargs))

    def __iter__(self):
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type == "StartTag":
                name = token["name"].lower()
                if name in allowedAttributeMap.keys():
                    allowedAttributes = allowedAttributeMap[name]
                    for attrName, attrValue in token["data"]:
                        if attrName.lower() not in allowedAttributes:
                            yield {"type": "ParseError",
                                   "data": "unrecognized-attribute",
                                   "datavars": {"tagName": name,
                                                "attributeName": attrName}}

            yield token
