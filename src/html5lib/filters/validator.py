"""HTML 5 conformance checker

Warning: this module is experimental, incomplete, and subject to removal at any time.

Usage:
>>> from html5lib.html5parser import HTMLParser
>>> from html5lib.filters.validator import HTMLConformanceChecker
>>> p = HTMLParser(tokenizer=HTMLConformanceChecker)
>>> p.parse('<!doctype html>\n<html foo=bar></html>')
<<class 'html5lib.treebuilders.simpletree.Document'> None>
>>> p.errors
[((2, 14), 'unknown-attribute', {'attributeName': u'foo', 'tagName': u'html'})]
"""

try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset
import _base
import iso639codes
import rfc3987
import rfc2046
from html5lib.constants import E, spaceCharacters, digits, tokenTypes
from html5lib import tokenizer
import gettext
_ = gettext.gettext

E.update({
    "unknown-start-tag":
        _(u"Unknown start tag <%(tagName)s>."),
    "unknown-attribute":
        _(u"Unknown '%(attributeName)s' attribute on <%(tagName)s>."),
    "missing-required-attribute":
        _(u"The '%(attributeName)s' attribute is required on <%(tagName)s>."),
    "unknown-input-type":
        _(u"Illegal value for attribute on <input type='%(inputType)s'>."),
    "attribute-not-allowed-on-this-input-type":
        _(u"The '%(attributeName)s' attribute is not allowed on <input type=%(inputType)s>."),
    "deprecated-attribute":
        _(u"This attribute is deprecated: '%(attributeName)s' attribute on <%(tagName)s>."),
    "duplicate-value-in-token-list":
        _(u"Duplicate value in token list: '%(attributeValue)s' in '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-attribute-value":
        _(u"Invalid attribute value: '%(attributeName)s' attribute on <%(tagName)s>."),
    "space-in-id":
        _(u"Whitespace is not allowed here: '%(attributeName)s' attribute on <%(tagName)s>."),
    "duplicate-id":
        _(u"This ID was already defined earlier: 'id' attribute on <%(tagName)s>."),
    "attribute-value-can-not-be-blank":
        _(u"This value can not be blank: '%(attributeName)s' attribute on <%(tagName)s>."),
    "id-does-not-exist":
        _(u"This value refers to a non-existent ID: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-enumerated-value":
        _(u"Value must be one of %(enumeratedValues)s: '%(attributeName)s' attribute on <%tagName)s>."),
    "invalid-boolean-value":
        _(u"Value must be one of %(enumeratedValues)s: '%(attributeName)s' attribute on <%tagName)s>."),
    "contextmenu-must-point-to-menu":
        _(u"The contextmenu attribute must point to an ID defined on a <menu> element."),
    "invalid-lang-code":
        _(u"Invalid language code: '%(attributeName)s' attibute on <%(tagName)s>."),
    "invalid-integer-value":
        _(u"Value must be an integer: '%(attributeName)s' attribute on <%tagName)s>."),
    "invalid-root-namespace":
        _(u"Root namespace must be 'http://www.w3.org/1999/xhtml', or omitted."),
    "invalid-browsing-context":
        _(u"Value must be one of ('_self', '_parent', '_top'), or a name that does not start with '_': '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-tag-uri":
        _(u"Invalid URI: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-urn":
        _(u"Invalid URN: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-uri-char":
        _(u"Illegal character in URI: '%(attributeName)s' attribute on <%(tagName)s>."),
    "uri-not-iri":
        _(u"Expected a URI but found an IRI: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-uri":
        _(u"Invalid URI: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-http-or-ftp-uri":
        _(u"Invalid URI: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-scheme":
        _(u"Unregistered URI scheme: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-rel":
        _(u"Invalid link relation: '%(attributeName)s' attribute on <%(tagName)s>."),
    "invalid-mime-type":
        _(u"Invalid MIME type: '%(attributeName)s' attribute on <%(tagName)s>."),
})

globalAttributes = frozenset(('class', 'contenteditable', 'contextmenu', 'dir',
    'draggable', 'id', 'irrelevant', 'lang', 'ref', 'tabindex', 'template', 
    'title', 'onabort', 'onbeforeunload', 'onblur', 'onchange', 'onclick',
    'oncontextmenu', 'ondblclick', 'ondrag', 'ondragend', 'ondragenter',
    'ondragleave', 'ondragover', 'ondragstart', 'ondrop', 'onerror', 
    'onfocus', 'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onmessage',
    'onmousedown', 'onmousemove', 'onmouseout', 'onmouseover', 'onmouseup',
    'onmousewheel', 'onresize', 'onscroll', 'onselect', 'onsubmit', 'onunload'))
# XXX lang in HTML only, xml:lang in XHTML only
# XXX validate ref, template

allowedAttributeMap = {
    'html': frozenset(('xmlns',)),
    'head': frozenset(()),
    'title': frozenset(()),
    'base': frozenset(('href', 'target')),
    'link': frozenset(('href', 'rel', 'media', 'hreflang', 'type')),
    'meta': frozenset(('name', 'http-equiv', 'content', 'charset')), # XXX charset in HTML only
    'style': frozenset(('media', 'type', 'scoped')),
    'body': frozenset(()),
    'section': frozenset(()),
    'nav': frozenset(()),
    'article': frozenset(()),
    'blockquote': frozenset(('cite',)),
    'aside': frozenset(()),
    'h1': frozenset(()),
    'h2': frozenset(()),
    'h3': frozenset(()),
    'h4': frozenset(()),
    'h5': frozenset(()),
    'h6': frozenset(()),
    'header': frozenset(()),
    'footer': frozenset(()),
    'address': frozenset(()),
    'p': frozenset(()),
    'hr': frozenset(()),
    'br': frozenset(()),
    'dialog': frozenset(()),
    'pre': frozenset(()),
    'ol': frozenset(('start',)),
    'ul': frozenset(()),
    'li': frozenset(('value',)), # XXX depends on parent
    'dl': frozenset(()),
    'dt': frozenset(()),
    'dd': frozenset(()),
    'a': frozenset(('href', 'target', 'ping', 'rel', 'media', 'hreflang', 'type')),
    'q': frozenset(('cite',)),
    'cite': frozenset(()),
    'em': frozenset(()),
    'strong': frozenset(()),
    'small': frozenset(()),
    'm': frozenset(()),
    'dfn': frozenset(()),
    'abbr': frozenset(()),
    'time': frozenset(('datetime',)),
    'meter': frozenset(('value', 'min', 'low', 'high', 'max', 'optimum')),
    'progress': frozenset(('value', 'max')),
    'code': frozenset(()),
    'var': frozenset(()),
    'samp': frozenset(()),
    'kbd': frozenset(()),
    'sup': frozenset(()),
    'sub': frozenset(()),
    'span': frozenset(()),
    'i': frozenset(()),
    'b': frozenset(()),
    'bdo': frozenset(()),
    'ins': frozenset(('cite', 'datetime')),
    'del': frozenset(('cite', 'datetime')),
    'figure': frozenset(()),
    'img': frozenset(('alt', 'src', 'usemap', 'ismap', 'height', 'width')), # XXX ismap depends on parent
    'iframe': frozenset(('src',)),
    # <embed> handled separately
    'object': frozenset(('data', 'type', 'usemap', 'height', 'width')),
    'param': frozenset(('name', 'value')),
    'video': frozenset(('src', 'autoplay', 'start', 'loopstart', 'loopend', 'end',
              'loopcount', 'controls')),
    'audio': frozenset(('src', 'autoplay', 'start', 'loopstart', 'loopend', 'end',
              'loopcount', 'controls')),
    'source': frozenset(('src', 'type', 'media')),
    'canvas': frozenset(('height', 'width')),
    'map': frozenset(()),
    'area': frozenset(('alt', 'coords', 'shape', 'href', 'target', 'ping', 'rel',
             'media', 'hreflang', 'type')),
    'table': frozenset(()),
    'caption': frozenset(()),
    'colgroup': frozenset(('span',)), # XXX only if element contains no <col> elements
    'col': frozenset(('span',)),
    'tbody': frozenset(()),
    'thead': frozenset(()),
    'tfoot': frozenset(()),
    'tr': frozenset(()),
    'td': frozenset(('colspan', 'rowspan')),
    'th': frozenset(('colspan', 'rowspan', 'scope')),
    # all possible <input> attributes are listed here but <input> is really handled separately
    'input': frozenset(('accept', 'accesskey', 'action', 'alt', 'autocomplete', 'autofocus', 'checked', 'disabled', 'enctype', 'form', 'inputmode', 'list', 'maxlength', 'method', 'min', 'max', 'name', 'pattern', 'step', 'readonly', 'replace', 'required', 'size', 'src', 'tabindex', 'target', 'template', 'value')),
    'form': frozenset(('action', 'method', 'enctype', 'accept', 'name', 'onsubmit',
             'onreset', 'accept-charset', 'data', 'replace')),
    'button': frozenset(('action', 'enctype', 'method', 'replace', 'template', 'name', 'value', 'type', 'disabled', 'form', 'autofocus')), # XXX may need matrix of acceptable attributes based on value of type attribute (like input)
    'select': frozenset(('name', 'size', 'multiple', 'disabled', 'data', 'accesskey',
               'form', 'autofocus')),
    'optgroup': frozenset(('disabled', 'label')),
    'option': frozenset(('selected', 'disabled', 'label', 'value')),
    'textarea': frozenset(('maxlength', 'name', 'rows', 'cols', 'disabled', 'readonly', 'required', 'form', 'autofocus', 'wrap', 'accept')),
    'label': frozenset(('for', 'accesskey', 'form')),
    'fieldset': frozenset(('disabled', 'form')),
    'output': frozenset(('form', 'name', 'for', 'onforminput', 'onformchange')),
    'datalist': frozenset(('data',)),
#    # XXX repetition model for repeating form controls
    'script': frozenset(('src', 'defer', 'async', 'type')),
    'noscript': frozenset(()),
    'noembed': frozenset(()),
    'event-source': frozenset(('src',)),
    'details': frozenset(('open',)),
    'datagrid': frozenset(('multiple', 'disabled')),
    'command': frozenset(('type', 'label', 'icon', 'hidden', 'disabled', 'checked',
                'radiogroup', 'default')),
    'menu': frozenset(('type', 'label', 'autosubmit')),
    'datatemplate': frozenset(()),
    'rule': frozenset(()),
    'nest': frozenset(()),
    'legend': frozenset(()),
    'div': frozenset(()),
    'font': frozenset(('style',))
}

requiredAttributeMap = {
    'link': frozenset(('href', 'rel')),
    'bdo': frozenset(('dir',)),
    'img': frozenset(('src',)),
    'embed': frozenset(('src',)),
    'object': frozenset(()), # XXX one of 'data' or 'type' is required
    'param': frozenset(('name', 'value')),
    'source': frozenset(('src',)),
    'map': frozenset(('id',))
}

inputTypeAllowedAttributeMap = {
    'text': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'inputmode', 'list', 'maxlength', 'name', 'pattern', 'readonly', 'required', 'size', 'tabindex', 'value')),
    'password': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'inputmode', 'maxlength', 'name', 'pattern', 'readonly', 'required', 'size', 'tabindex', 'value')),
    'checkbox': frozenset(('accesskey', 'autofocus', 'checked', 'disabled', 'form', 'name', 'required', 'tabindex', 'value')),
    'radio': frozenset(('accesskey', 'autofocus', 'checked', 'disabled', 'form', 'name', 'required', 'tabindex', 'value')),
    'button': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'value')),
    'submit': frozenset(('accesskey', 'action', 'autofocus', 'disabled', 'enctype', 'form', 'method', 'name', 'replace', 'tabindex', 'target', 'value')),
    'reset': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'value')),
    'add': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'template', 'value')),
    'remove': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'value')),
    'move-up': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'value')),
    'move-down': frozenset(('accesskey', 'autofocus', 'disabled', 'form', 'name', 'tabindex', 'value')),
    'file': frozenset(('accept', 'accesskey', 'autofocus', 'disabled', 'form', 'min', 'max', 'name', 'required', 'tabindex')),
    'hidden': frozenset(('disabled', 'form', 'name', 'value')),
    'image': frozenset(('accesskey', 'action', 'alt', 'autofocus', 'disabled', 'enctype', 'form', 'method', 'name', 'replace', 'src', 'tabindex', 'target')),
    'datetime': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'datetime-local': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'date': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'month': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'week': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'time': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'number': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'range': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'list', 'min', 'max', 'name', 'step', 'readonly', 'required', 'tabindex', 'value')),
    'email': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'inputmode', 'list', 'maxlength', 'name', 'pattern', 'readonly', 'required', 'tabindex', 'value')),
    'url': frozenset(('accesskey', 'autocomplete', 'autofocus', 'disabled', 'form', 'inputmode', 'list', 'maxlength', 'name', 'pattern', 'readonly', 'required', 'tabindex', 'value'))
}

inputTypeDeprecatedAttributeMap = {
    'text': frozenset(('size',)),
    'password': frozenset(('size',))
}

linkRelValues = frozenset(('alternate', 'archive', 'archives', 'author', 'contact', 'feed', 'first', 'begin', 'start', 'help', 'icon', 'index', 'top', 'contents', 'toc', 'last', 'end', 'license', 'copyright', 'next', 'pingback', 'prefetch', 'prev', 'previous', 'search', 'stylesheet', 'sidebar', 'tag', 'up'))
aRelValues = frozenset(('alternate', 'archive', 'archives', 'author', 'contact', 'feed', 'first', 'begin', 'start', 'help', 'index', 'top', 'contents', 'toc', 'last', 'end', 'license', 'copyright', 'next', 'prev', 'previous', 'search', 'sidebar', 'tag', 'up', 'bookmark', 'external', 'nofollow'))

class HTMLConformanceChecker(_base.Filter):
    def __init__(self, stream, encoding, parseMeta, **kwargs):
        _base.Filter.__init__(self, tokenizer.HTMLTokenizer(
            stream, encoding, parseMeta, **kwargs))
        self.thingsThatDefineAnID = []
        self.thingsThatPointToAnID = []
        self.IDsWeHaveKnownAndLoved = []

    def __iter__(self):
        types = dict((v,k) for k,v in tokenTypes.iteritems())
        for token in _base.Filter.__iter__(self):
            fakeToken = {"type": types.get(token.get("type", "-"), "-"),
                         "name": token.get("name", "-").capitalize()}
            method = getattr(self, "validate%(type)s%(name)s" % fakeToken, None)
            if method:
                for t in method(token) or []: yield t
            else:
                method = getattr(self, "validate%(type)s" % fakeToken, None)
                if method:
                    for t in method(token) or []: yield t
            yield token
        for t in self.eof() or []: yield t

    ##########################################################################
    # Start tag validation
    ##########################################################################

    def validateStartTag(self, token):
        for t in self.checkUnknownStartTag(token) or []: yield t
        for t in self.checkStartTagRequiredAttributes(token) or []: yield t
        for t in self.checkStartTagUnknownAttributes(token) or []: yield t
        for t in self.checkAttributeValues(token) or []: yield t

    def validateStartTagEmbed(self, token):
        for t in self.checkStartTagRequiredAttributes(token) or []: yield t
        for t in self.checkAttributeValues(token) or []: yield t
        # spec says "any attributes w/o namespace"
        # so don't call checkStartTagUnknownAttributes

    def validateStartTagInput(self, token):
        for t in self.checkAttributeValues(token) or []: yield t
        attrDict = dict([(name.lower(), value) for name, value in token.get("data", [])])
        inputType = attrDict.get("type", "text")
        if inputType not in inputTypeAllowedAttributeMap.keys():
            yield {"type": tokenTypes["ParseError"],
                   "data": "unknown-input-type",
                   "datavars": {"attrValue": inputType}}
        allowedAttributes = inputTypeAllowedAttributeMap.get(inputType, [])
        for attrName, attrValue in attrDict.items():
            if attrName not in allowedAttributeMap['input']:
                yield {"type": tokenTypes["ParseError"],
                       "data": "unknown-attribute",
                       "datavars": {"tagName": "input",
                                    "attributeName": attrName}}
            elif attrName not in allowedAttributes:
                yield {"type": tokenTypes["ParseError"],
                       "data": "attribute-not-allowed-on-this-input-type",
                       "datavars": {"attributeName": attrName,
                                    "inputType": inputType}}
            if attrName in inputTypeDeprecatedAttributeMap.get(inputType, []):
                yield {"type": tokenTypes["ParseError"],
                       "data": "deprecated-attribute",
                       "datavars": {"attributeName": attrName,
                                    "inputType": inputType}}

    ##########################################################################
    # Start tag validation helpers
    ##########################################################################

    def checkUnknownStartTag(self, token):
        # check for recognized tag name
        name = token.get("name", "").lower()
        if name not in allowedAttributeMap.keys():
            yield {"type": tokenTypes["ParseError"],
                   "data": "unknown-start-tag",
                   "datavars": {"tagName": name}}

    def checkStartTagRequiredAttributes(self, token):
        # check for presence of required attributes
        name = token.get("name", "").lower()
        if name in requiredAttributeMap.keys():
            attrsPresent = [attrName for attrName, attrValue
                            in token.get("data", [])]
            for attrName in requiredAttributeMap[name]:
                if attrName not in attrsPresent:
                    yield {"type": tokenTypes["ParseError"],
                           "data": "missing-required-attribute",
                           "datavars": {"tagName": name,
                                        "attributeName": attrName}}

    def checkStartTagUnknownAttributes(self, token):
        # check for recognized attribute names
        name = token.get("name").lower()
        allowedAttributes = globalAttributes | allowedAttributeMap.get(name, frozenset(()))
        for attrName, attrValue in token.get("data", []):
            if attrName.lower() not in allowedAttributes:
                yield {"type": tokenTypes["ParseError"],
                       "data": "unknown-attribute",
                       "datavars": {"tagName": name,
                                    "attributeName": attrName}}

    ##########################################################################
    # Attribute validation helpers
    ##########################################################################

#    def checkURI(self, token, tagName, attrName, attrValue):
#        isValid, errorCode = rfc3987.isValidURI(attrValue)
#        if not isValid:
#            yield {"type": tokenTypes["ParseError"],
#                   "data": errorCode,
#                   "datavars": {"tagName": tagName,
#                                "attributeName": attrName}}
#            yield {"type": tokenTypes["ParseError"],
#                   "data": "invalid-attribute-value",
#                   "datavars": {"tagName": tagName,
#                                "attributeName": attrName}}

    def checkIRI(self, token, tagName, attrName, attrValue):
        isValid, errorCode = rfc3987.isValidIRI(attrValue)
        if not isValid:
            yield {"type": tokenTypes["ParseError"],
                   "data": errorCode,
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-attribute-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

    def checkID(self, token, tagName, attrName, attrValue):
        if not attrValue:
            yield {"type": tokenTypes["ParseError"],
                   "data": "attribute-value-can-not-be-blank",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}
        for c in attrValue:
            if c in spaceCharacters:
                yield {"type": tokenTypes["ParseError"],
                       "data": "space-in-id",
                       "datavars": {"tagName": tagName,
                                    "attributeName": attrName}}
                yield {"type": tokenTypes["ParseError"],
                       "data": "invalid-attribute-value",
                       "datavars": {"tagName": tagName,
                                    "attributeName": attrName}}
                break
        
    def parseTokenList(self, value):
        valueList = []
        currentValue = ''
        for c in value + ' ':
            if c in spaceCharacters:
                if currentValue:
                    valueList.append(currentValue)
                    currentValue = ''
            else:
                currentValue += c
        if currentValue:
            valueList.append(currentValue)
        return valueList
        
    def checkTokenList(self, tagName, attrName, attrValue):
        # The "token" in the method name refers to tokens in an attribute value
        # i.e. http://www.whatwg.org/specs/web-apps/current-work/#set-of
        # but the "token" parameter refers to the token generated from
        # HTMLTokenizer.  Sorry for the confusion.
        valueList = self.parseTokenList(attrValue)
        valueDict = {}
        for currentValue in valueList:
            if valueDict.has_key(currentValue):
                yield {"type": tokenTypes["ParseError"],
                       "data": "duplicate-value-in-token-list",
                       "datavars": {"tagName": tagName,
                                    "attributeName": attrName,
                                    "attributeValue": currentValue}}
                break
            valueDict[currentValue] = 1

    def checkEnumeratedValue(self, token, tagName, attrName, attrValue, enumeratedValues):
        if not attrValue and ('' not in enumeratedValues):
            yield {"type": tokenTypes["ParseError"],
                   "data": "attribute-value-can-not-be-blank",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}
            return
        attrValue = attrValue.lower()
        if attrValue not in enumeratedValues:
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-enumerated-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName,
                                "enumeratedValues": tuple(enumeratedValues)}}
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-attribute-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}
        
    def checkBoolean(self, token, tagName, attrName, attrValue):
        enumeratedValues = frozenset((attrName, ''))
        if attrValue not in enumeratedValues:
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-boolean-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName,
                                "enumeratedValues": tuple(enumeratedValues)}}
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-attribute-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

    def checkInteger(self, token, tagName, attrName, attrValue):
        sign = 1
        numberString = ''
        state = 'begin' # ('begin', 'initial-number', 'number', 'trailing-junk')
        error = {"type": tokenTypes["ParseError"],
                 "data": "invalid-integer-value",
                 "datavars": {"tagName": tagName,
                              "attributeName": attrName,
                              "attributeValue": attrValue}}
        for c in attrValue:
            if state == 'begin':
                if c in spaceCharacters:
                    pass
                elif c == '-':
                    sign = -1
                    state = 'initial-number'
                elif c in digits:
                    numberString += c
                    state = 'in-number'
                else:
                    yield error
                    return
            elif state == 'initial-number':
                if c not in digits:
                    yield error
                    return
                numberString += c
                state = 'in-number'
            elif state == 'in-number':
                if c in digits:
                    numberString += c
                else:
                    state = 'trailing-junk'
            elif state == 'trailing-junk':
                pass
        if not numberString:
            yield {"type": tokenTypes["ParseError"],
                   "data": "attribute-value-can-not-be-blank",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

    def checkFloatingPointNumber(self, token, tagName, attrName, attrValue):
        # XXX
        pass

    def checkBrowsingContext(self, token, tagName, attrName, attrValue):
        if not attrValue: return
        if attrValue[0] != '_': return
        attrValue = attrValue.lower()
        if attrValue in frozenset(('_self', '_parent', '_top', '_blank')): return
        yield {"type": tokenTypes["ParseError"],
               "data": "invalid-browsing-context",
               "datavars": {"tagName": tagName,
                            "attributeName": attrName}}

    def checkLangCode(self, token, tagName, attrName, attrValue):
        if not attrValue: return # blank is OK
        if not iso639codes.isValidLangCode(attrValue):
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-lang-code",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName,
                                "attributeValue": attrValue}}

    def checkMIMEType(self, token, tagName, attrName, attrValue):
        # XXX needs tests
        if not attrValue:
            yield {"type": tokenTypes["ParseError"],
                   "data": "attribute-value-can-not-be-blank",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

        if not rfc2046.isValidMIMEType(attrValue):
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-mime-type",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName,
                                "attributeValue": attrValue}}

    def checkMediaQuery(self, token, tagName, attrName, attrValue):
        # XXX
        pass

    def checkLinkRelation(self, token, tagName, attrName, attrValue):
        for t in self.checkTokenList(tagName, attrName, attrValue) or []: yield t
        valueList = self.parseTokenList(attrValue)
        allowedValues = (tagName == 'link') and linkRelValues or aRelValues
        for currentValue in valueList:
            if currentValue not in allowedValues:
                yield {"type": tokenTypes["ParseError"],
                       "data": "invalid-rel",
                       "datavars": {"tagName": tagName,
                                    "attributeName": attrName}}

    def checkDateTime(self, token, tagName, attrName, attrValue):
        # XXX
        state = 'begin' # ('begin', '...
#        for c in attrValue:
#            if state == 'begin':
#                if c in spaceCharacters:
#                    continue
#                elif c in digits:
#                    state = ...
                    

    ##########################################################################
    # Attribute validation
    ##########################################################################

    def checkAttributeValues(self, token):
        tagName = token.get("name", "")
        fakeToken = {"tagName": tagName.capitalize()}
        for attrName, attrValue in token.get("data", []):
            attrName = attrName.lower()
            fakeToken["attributeName"] = attrName.capitalize()
            method = getattr(self, "validateAttributeValue%(tagName)s%(attributeName)s" % fakeToken, None)
            if method:
                for t in method(token, tagName, attrName, attrValue) or []: yield t
            else:
                method = getattr(self, "validateAttributeValue%(attributeName)s" % fakeToken, None)
                if method:
                    for t in method(token, tagName, attrName, attrValue) or []: yield t

    def validateAttributeValueClass(self, token, tagName, attrName, attrValue):
        for t in self.checkTokenList(tagName, attrName, attrValue) or []:
            yield t
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-attribute-value",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

    def validateAttributeValueContenteditable(self, token, tagName, attrName, attrValue):
        for t in self.checkEnumeratedValue(token, tagName, attrName, attrValue, frozenset(('true', 'false', ''))) or []: yield t

    def validateAttributeValueDir(self, token, tagName, attrName, attrValue):
        for t in self.checkEnumeratedValue(token, tagName, attrName, attrValue, frozenset(('ltr', 'rtl'))) or []: yield t

    def validateAttributeValueDraggable(self, token, tagName, attrName, attrValue):
        for t in self.checkEnumeratedValue(token, tagName, attrName, attrValue, frozenset(('true', 'false'))) or []: yield t

    validateAttributeValueIrrelevant = checkBoolean
    validateAttributeValueLang = checkLangCode

    def validateAttributeValueContextmenu(self, token, tagName, attrName, attrValue):
        for t in self.checkID(token, tagName, attrName, attrValue) or []: yield t
        self.thingsThatPointToAnID.append(token)

    def validateAttributeValueId(self, token, tagName, attrName, attrValue):
        # This method has side effects.  It adds 'token' to the list of
        # things that define an ID (self.thingsThatDefineAnID) so that we can
        # later check 1) whether an ID is duplicated, and 2) whether all the
        # things that point to something else by ID (like <label for> or
        # <span contextmenu>) point to an ID that actually exists somewhere.
        for t in self.checkID(token, tagName, attrName, attrValue) or []: yield t
        if not attrValue: return
        if attrValue in self.IDsWeHaveKnownAndLoved:
            yield {"type": tokenTypes["ParseError"],
                   "data": "duplicate-id",
                   "datavars": {"tagName": tagName}}
        self.IDsWeHaveKnownAndLoved.append(attrValue)
        self.thingsThatDefineAnID.append(token)

    validateAttributeValueTabindex = checkInteger

    def validateAttributeValueRef(self, token, tagName, attrName, attrValue):
        # XXX
        pass

    def validateAttributeValueTemplate(self, token, tagName, attrName, attrValue):
        # XXX
        pass

    def validateAttributeValueHtmlXmlns(self, token, tagName, attrName, attrValue):
        if attrValue != "http://www.w3.org/1999/xhtml":
            yield {"type": tokenTypes["ParseError"],
                   "data": "invalid-root-namespace",
                   "datavars": {"tagName": tagName,
                                "attributeName": attrName}}

    validateAttributeValueBaseHref = checkIRI
    validateAttributeValueBaseTarget = checkBrowsingContext
    validateAttributeValueLinkHref = checkIRI
    validateAttributeValueLinkRel = checkLinkRelation
    validateAttributeValueLinkMedia = checkMediaQuery
    validateAttributeValueLinkHreflang = checkLangCode
    validateAttributeValueLinkType = checkMIMEType
    # XXX <meta> attributes
    validateAttributeValueStyleMedia = checkMediaQuery
    validateAttributeValueStyleType = checkMIMEType
    validateAttributeValueStyleScoped = checkBoolean
    validateAttributeValueBlockquoteCite = checkIRI
    validateAttributeValueOlStart = checkInteger
    validateAttributeValueLiValue = checkInteger
    # XXX need tests from here on
    validateAttributeValueAHref = checkIRI
    validateAttributeValueATarget = checkBrowsingContext

    def validateAttributeValueAPing(self, token, tagName, attrName, attrValue):
        valueList = self.parseTokenList(attrValue)
        for currentValue in valueList:
            for t in self.checkIRI(token, tagName, attrName, attrValue) or []: yield t

    validateAttributeValueARel = checkLinkRelation
    validateAttributeValueAMedia = checkMediaQuery
    validateAttributeValueAHreflang = checkLangCode
    validateAttributeValueAType = checkMIMEType
    validateAttributeValueQCite = checkIRI
    validateAttributeValueTimeDatetime = checkDateTime
    validateAttributeValueMeterValue = checkFloatingPointNumber
    validateAttributeValueMeterMin = checkFloatingPointNumber
    validateAttributeValueMeterLow = checkFloatingPointNumber
    validateAttributeValueMeterHigh = checkFloatingPointNumber
    validateAttributeValueMeterMax = checkFloatingPointNumber
    validateAttributeValueMeterOptimum = checkFloatingPointNumber
    validateAttributeValueProgressValue = checkFloatingPointNumber
    validateAttributeValueProgressMax = checkFloatingPointNumber
    validateAttributeValueInsCite = checkIRI
    validateAttributeValueInsDatetime = checkDateTime
    validateAttributeValueDelCite = checkIRI
    validateAttributeValueDelDatetime = checkDateTime

    ##########################################################################
    # Whole document validation (IDs, etc.)
    ##########################################################################

    def eof(self):
        for token in self.thingsThatPointToAnID:
            tagName = token.get("name", "").lower()
            attrsDict = token["data"] # by now html5parser has "normalized" the attrs list into a dict.
                                      # hooray for obscure side effects!
            attrValue = attrsDict.get("contextmenu", "")
            if attrValue and (attrValue not in self.IDsWeHaveKnownAndLoved):
                yield {"type": tokenTypes["ParseError"],
                       "data": "id-does-not-exist",
                       "datavars": {"tagName": tagName,
                                    "attributeName": "contextmenu",
                                    "attributeValue": attrValue}}
            else:
                for refToken in self.thingsThatDefineAnID:
                    id = refToken.get("data", {}).get("id", "")
                    if not id: continue
                    if id == attrValue:
                        if refToken.get("name", "").lower() != "menu":
                            yield {"type": tokenTypes["ParseError"],
                                   "data": "contextmenu-must-point-to-menu"}
                        break
