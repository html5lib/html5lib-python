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
    "missing-required-attribute":
        _(u"Missing required attribute '%(attributeName)s' in <%(tagName)s>"),
})

globalAttributes = ['class', 'contenteditable', 'contextmenu', 'dir',
    'draggable', 'id', 'irrelevant', 'lang', 'ref', 'tabindex', 'template', 
    'title', 'onabort', 'onbeforeunload', 'onblur', 'onchange', 'onclick',
    'oncontextmenu', 'ondblclick', 'ondrag', 'ondragend', 'ondragenter',
    'ondragleave', 'ondragover', 'ondragstart', 'ondrop', 'onerror', 
    'onfocus', 'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onmessage',
    'onmousedown', 'onmousemove', 'onmouseout', 'onmouseover', 'onmouseup',
    'onmousewheel', 'onresize', 'onscroll', 'onselect', 'onsubmit', 'onunload']
# XXX lang in HTML only, xml:lang in XHTML only

allowedAttributeMap = {
    'html': ['xmlns'],
    'base': ['href', 'target'],
    'link': ['href', 'rel', 'media', 'hreflang', 'type'],
    'meta': ['name', 'http-equiv', 'content', 'charset'], # XXX charset in HTML only
    'style': ['media', 'type', 'scoped'],
    'blockquote': ['cite'],
    'ol': ['start'],
    'li': ['value'], # XXX depends on parent
    'a': ['href', 'target', 'ping', 'rel', 'media', 'hreflang', 'type'],
    'q': ['cite'],
    'time': ['datetime'],
    'meter': ['value', 'min', 'low', 'high', 'max', 'optimum'],
    'progress': ['value', 'max'],
    'ins': ['cite', 'datetime'],
    'del': ['cite', 'datetime'],
    'img': ['alt', 'src', 'usemap', 'ismap', 'height', 'width'], # XXX ismap depends on parent
    'iframe': ['src'],
    'object': ['data', 'type', 'usemap', 'height', 'width'],
    'param': ['name', 'value'],
    'video': ['src', 'autoplay', 'start', 'loopstart', 'loopend', 'end',
              'loopcount', 'controls'],
    'audio': ['src', 'autoplay', 'start', 'loopstart', 'loopend', 'end',
              'loopcount', 'controls'],
    'source': ['src', 'type', 'media'],
    'canvas': ['height', 'width'],
    'area': ['alt', 'coords', 'shape', 'href', 'target', 'ping', 'rel',
             'media', 'hreflang', 'type'],
    'colgroup': ['span'], # XXX only if element contains no <col> elements
    'col': ['span'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan', 'scope'],
    # XXX form elements
    'script': ['src', 'defer', 'async', 'type'],
    'event-source': ['src'],
    'details': ['open'],
    'datagrid': ['multiple', 'disabled'],
    'command': ['type', 'label', 'icon', 'hidden', 'disabled', 'checked',
                'radiogroup', 'default'],
    'menu': ['type', 'label', 'autosubmit'],
    'font': ['style']
}

requiredAttributeMap = {
    'link': ['href', 'rel'],
    'bdo': ['dir'],
    'img': ['src'],
    'embed': ['src'],
    'object': [], # XXX one of 'data' or 'type' is required
    'param': ['name', 'value'],
    'source': ['src'],
    'map': ['id'],
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
                if name == 'embed':
                    # XXX spec says "any attributes w/o namespace"
                    pass
                else:
                    if name in allowedAttributeMap.keys():
                        allowedAttributes = globalAttributes + \
                            allowedAttributeMap[name]
                    else:
                        allowedAttributes = globalAttributes
                    for attrName, attrValue in token["data"]:
                        if attrName.lower() not in allowedAttributes:
                            yield {"type": "ParseError",
                                   "data": "unrecognized-attribute",
                                   "datavars": {"tagName": name,
                                                "attributeName": attrName}}
                if name in requiredAttributeMap.keys():
                    attrsPresent = [attrName for attrName, attrValue
                                    in token["data"]]
                    for attrName in requiredAttributeMap[name]:
                        if attrName not in attrsPresent:
                            yield {"type": "ParseError",
                                   "data": "missing-required-attribute",
                                   "datavars": {"tagName": name,
                                                "attributeName": attrName}}
            yield token
