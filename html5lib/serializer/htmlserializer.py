from __future__ import absolute_import
import gettext
_ = gettext.gettext

try:
    pass # no-op statement to avoid 3to2 introducing parse error
except ImportError:
    pass

from html5lib.constants import voidElements, booleanAttributes, spaceCharacters
from html5lib.constants import rcdataElements, entities, xmlEntities
from html5lib import utils
from xml.sax.saxutils import escape

spaceCharacters = u"".join(spaceCharacters)

try:
    from codecs import register_error, xmlcharrefreplace_errors
except ImportError:
    unicode_encode_errors = u"strict"
else:
    unicode_encode_errors = u"htmlentityreplace"

    from html5lib.constants import entities

    encode_entity_map = {}
    is_ucs4 = len(u"\U0010FFFF") == 1
    for k, v in list(entities.items()):
        #skip multi-character entities
        if ((is_ucs4 and len(v) > 1) or
            (not is_ucs4 and len(v) > 2)):
            continue
        if v != u"&":
            if len(v) == 2:
                v = utils.surrogatePairToCodepoint(v)
            else:
                try:
                    v = ord(v)
                except:
                    print v
                    raise
            if not v in encode_entity_map or k.islower():
                # prefer &lt; over &LT; and similarly for &amp;, &gt;, etc.
                encode_entity_map[v] = k

    def htmlentityreplace_errors(exc):
        if isinstance(exc, (UnicodeEncodeError, UnicodeTranslateError)):
            res = []
            codepoints = []
            skip = False
            for i, c in enumerate(exc.object[exc.start:exc.end]):
                if skip:
                    skip = False
                    continue
                index = i + exc.start
                if utils.isSurrogatePair(exc.object[index:min([exc.end, index+2])]):
                    codepoint = utils.surrogatePairToCodepoint(exc.object[index:index+2])
                    skip = True
                else:
                    codepoint = ord(c)
                codepoints.append(codepoint)
            for cp in codepoints:
                e = encode_entity_map.get(cp)
                if e:
                    res.append(u"&")
                    res.append(e)
                    if not e.endswith(u";"):
                        res.append(u";")
                else:
                    res.append(u"&#x%s;"%(hex(cp)[2:]))
            return (u"".join(res), exc.end)
        else:
            return xmlcharrefreplace_errors(exc)
    htmlentityreplace_errors.func_annotations = {}

    register_error(unicode_encode_errors, htmlentityreplace_errors)

    del register_error


class HTMLSerializer(object):

    # attribute quoting options
    quote_attr_values = False
    quote_char = u'"'
    use_best_quote_char = True

    # tag syntax options
    omit_optional_tags = True
    minimize_boolean_attributes = True
    use_trailing_solidus = False
    space_before_trailing_solidus = True

    # escaping options
    escape_lt_in_attrs = False
    escape_rcdata = False
    resolve_entities = True

    # miscellaneous options
    inject_meta_charset = True
    strip_whitespace = False
    sanitize = False

    options = (u"quote_attr_values", u"quote_char", u"use_best_quote_char",
          u"minimize_boolean_attributes", u"use_trailing_solidus",
          u"space_before_trailing_solidus", u"omit_optional_tags",
          u"strip_whitespace", u"inject_meta_charset", u"escape_lt_in_attrs",
          u"escape_rcdata", u"resolve_entities", u"sanitize")

    def __init__(self, **kwargs):
        u"""Initialize HTMLSerializer.

        Keyword options (default given first unless specified) include:

        inject_meta_charset=True|False
          Whether it insert a meta element to define the character set of the
          document.
        quote_attr_values=True|False
          Whether to quote attribute values that don't require quoting
          per HTML5 parsing rules.
        quote_char=u'"'|u"'"
          Use given quote character for attribute quoting. Default is to
          use double quote unless attribute value contains a double quote,
          in which case single quotes are used instead.
        escape_lt_in_attrs=False|True
          Whether to escape < in attribute values.
        escape_rcdata=False|True
          Whether to escape characters that need to be escaped within normal
          elements within rcdata elements such as style.
        resolve_entities=True|False
          Whether to resolve named character entities that appear in the
          source tree. The XML predefined entities &lt; &gt; &amp; &quot; &apos;
          are unaffected by this setting.
        strip_whitespace=False|True
          Whether to remove semantically meaningless whitespace. (This
          compresses all whitespace to a single space except within pre.)
        minimize_boolean_attributes=True|False
          Shortens boolean attributes to give just the attribute value,
          for example <input disabled="disabled"> becomes <input disabled>.
        use_trailing_solidus=False|True
          Includes a close-tag slash at the end of the start tag of void
          elements (empty elements whose end tag is forbidden). E.g. <hr/>.
        space_before_trailing_solidus=True|False
          Places a space immediately before the closing slash in a tag
          using a trailing solidus. E.g. <hr />. Requires use_trailing_solidus.
        sanitize=False|True
          Strip all unsafe or unknown constructs from output.
          See `html5lib user documentation`_
        omit_optional_tags=True|False
          Omit start/end tags that are optional.

        .. _html5lib user documentation: http://code.google.com/p/html5lib/wiki/UserDocumentation
        """
        if u'quote_char' in kwargs:
            self.use_best_quote_char = False
        for attr in self.options:
            setattr(self, attr, kwargs.get(attr, getattr(self, attr)))
        self.errors = []
        self.strict = False
    __init__.func_annotations = {}

    def encode(self, string):
        assert(isinstance(string, unicode))
        if self.encoding:
            return string.encode(self.encoding, unicode_encode_errors)
        else:
            return string
    encode.func_annotations = {}

    def encodeStrict(self, string):
        assert(isinstance(string, unicode))
        if self.encoding:
            return string.encode(self.encoding, u"strict")
        else:
            return string
    encodeStrict.func_annotations = {}

    def serialize(self, treewalker, encoding=None):
        self.encoding = encoding
        in_cdata = False
        self.errors = []
        if encoding and self.inject_meta_charset:
            from html5lib.filters.inject_meta_charset import Filter
            treewalker = Filter(treewalker, encoding)
        # XXX: WhitespaceFilter should be used before OptionalTagFilter
        # for maximum efficiently of this latter filter
        if self.strip_whitespace:
            from html5lib.filters.whitespace import Filter
            treewalker = Filter(treewalker)
        if self.sanitize:
            from html5lib.filters.sanitizer import Filter
            treewalker = Filter(treewalker)
        if self.omit_optional_tags:
            from html5lib.filters.optionaltags import Filter
            treewalker = Filter(treewalker)
        for token in treewalker:
            type = token[u"type"]
            if type == u"Doctype":
                doctype = u"<!DOCTYPE %s" % token[u"name"]
                
                if token[u"publicId"]:
                    doctype += u' PUBLIC "%s"' % token[u"publicId"]
                elif token[u"systemId"]:
                    doctype += u" SYSTEM"
                if token[u"systemId"]:                
                    if token[u"systemId"].find(u'"') >= 0:
                        if token[u"systemId"].find(u"'") >= 0:
                            self.serializeError(_(u"System identifer contains both single and double quote characters"))
                        quote_char = u"'"
                    else:
                        quote_char = u'"'
                    doctype += u" %s%s%s" % (quote_char, token[u"systemId"], quote_char)
                
                doctype += u">"
                yield self.encodeStrict(doctype)

            elif type in (u"Characters", u"SpaceCharacters"):
                if type == u"SpaceCharacters" or in_cdata:
                    if in_cdata and token[u"data"].find(u"</") >= 0:
                        self.serializeError(_(u"Unexpected </ in CDATA"))
                    yield self.encode(token[u"data"])
                else:
                    yield self.encode(escape(token[u"data"]))

            elif type in (u"StartTag", u"EmptyTag"):
                name = token[u"name"]
                yield self.encodeStrict(u"<%s" % name)
                if name in rcdataElements and not self.escape_rcdata:
                    in_cdata = True
                elif in_cdata:
                    self.serializeError(_(u"Unexpected child element of a CDATA element"))
                attributes = []
                for (attr_namespace,attr_name),attr_value in sorted(token[u"data"].items()):
                    #TODO: Add namespace support here
                    k = attr_name
                    v = attr_value
                    yield self.encodeStrict(u' ')

                    yield self.encodeStrict(k)
                    if not self.minimize_boolean_attributes or \
                      (k not in booleanAttributes.get(name, tuple()) \
                      and k not in booleanAttributes.get(u"", tuple())):
                        yield self.encodeStrict(u"=")
                        if self.quote_attr_values or not v:
                            quote_attr = True
                        else:
                            quote_attr = reduce(lambda x,y: x or (y in v),
                                spaceCharacters + u">\"'=", False)
                        v = v.replace(u"&", u"&amp;")
                        if self.escape_lt_in_attrs: v = v.replace(u"<", u"&lt;")
                        if quote_attr:
                            quote_char = self.quote_char
                            if self.use_best_quote_char:
                                if u"'" in v and u'"' not in v:
                                    quote_char = u'"'
                                elif u'"' in v and u"'" not in v:
                                    quote_char = u"'"
                            if quote_char == u"'":
                                v = v.replace(u"'", u"&#39;")
                            else:
                                v = v.replace(u'"', u"&quot;")
                            yield self.encodeStrict(quote_char)
                            yield self.encode(v)
                            yield self.encodeStrict(quote_char)
                        else:
                            yield self.encode(v)
                if name in voidElements and self.use_trailing_solidus:
                    if self.space_before_trailing_solidus:
                        yield self.encodeStrict(u" /")
                    else:
                        yield self.encodeStrict(u"/")
                yield self.encode(u">")

            elif type == u"EndTag":
                name = token[u"name"]
                if name in rcdataElements:
                    in_cdata = False
                elif in_cdata:
                    self.serializeError(_(u"Unexpected child element of a CDATA element"))
                yield self.encodeStrict(u"</%s>" % name)

            elif type == u"Comment":
                data = token[u"data"]
                if data.find(u"--") >= 0:
                    self.serializeError(_(u"Comment contains --"))
                yield self.encodeStrict(u"<!--%s-->" % token[u"data"])

            elif type == u"Entity":
                name = token[u"name"]
                key = name + u";"
                if not key in entities:
                    self.serializeError(_(u"Entity %s not recognized" % name))
                if self.resolve_entities and key not in xmlEntities:
                    data = entities[key]
                else:
                    data = u"&%s;" % name
                yield self.encodeStrict(data)

            else:
                self.serializeError(token[u"data"])
    serialize.func_annotations = {}

    def render(self, treewalker, encoding=None):
        if encoding:
            return "".join(list(self.serialize(treewalker, encoding)))
        else:
            return u"".join(list(self.serialize(treewalker)))
    render.func_annotations = {}

    def serializeError(self, data=u"XXX ERROR MESSAGE NEEDED"):
        # XXX The idea is to make data mandatory.
        self.errors.append(data)
        if self.strict:
            raise SerializeError
    serializeError.func_annotations = {}

def SerializeError(Exception):
    u"""Error in serialized tree"""
    pass
SerializeError.func_annotations = {}
