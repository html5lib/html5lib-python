try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import ImmutableSet as frozenset

import gettext
_ = gettext.gettext

from html5lib.constants import voidElements, booleanAttributes, spaceCharacters
from html5lib.constants import rcdataElements, entities, xmlEntities
from html5lib import utils
from xml.sax.saxutils import escape

import re

spaceCharacters = u"".join(spaceCharacters)

try:
    from codecs import register_error, xmlcharrefreplace_errors
except ImportError:
    unicode_encode_errors = "strict"
else:
    unicode_encode_errors = "htmlentityreplace"

    from html5lib.constants import entities

    encode_entity_map = {}
    for k, v in entities.items():
        if v != "&" and encode_entity_map.get(v) != k.lower():
            # prefer &lt; over &LT; and similarly for &amp;, &gt;, etc.
            encode_entity_map[ord(v)] = k

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
                    res.append("&")
                    res.append(e)
                    if not e.endswith(";"):
                        res.append(";")
                else:
                    res.append("&#x%s;"%(hex(cp)[2:]))
            return (u"".join(res), exc.end)
        else:
            return xmlcharrefreplace_errors(exc)

    register_error(unicode_encode_errors, htmlentityreplace_errors)

    del register_error

def encode(text, encoding):
    return text.encode(encoding, unicode_encode_errors)

class HTMLSerializer(object):

    # attribute quoting options
    quote_attr_values = False
    quote_char = '"'
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
    emit_doctype = 'preserve'
    inject_meta_charset = True
    lang_attr = 'preserve'
    strip_whitespace = False
    sanitize = False

    options = ("quote_attr_values", "quote_char", "use_best_quote_char",
          "minimize_boolean_attributes", "use_trailing_solidus",
          "space_before_trailing_solidus", "omit_optional_tags",
          "strip_whitespace", "inject_meta_charset", "escape_lt_in_attrs",
          "escape_rcdata", "resolve_entities", "emit_doctype", "lang_attr",
          "sanitize")

    def __init__(self, **kwargs):
        """Initialize HTMLSerializer.

        Keyword options (default given first unless specified) include:

        emit_doctype='html'|'xhtml'|'html5'|'preserve'
          Whether to output a doctype.
            * emit_doctype='xhtml' preserves unknown doctypes and valid
              XHTML doctypes, converts valid HTML doctypes to their XHTML
              counterparts, and drops <!DOCTYPE html>
            * emit_doctype='html' preserves unknown doctypes and valid
              HTML doctypes, converts valid XHTML doctypes to their HTML
              counterparts, and uses <!DOCTYPE html> for missing doctypes
            * emit_doctype='html5' Uses <!DOCTYPE html> as the doctype
            * emit_doctype='preserve' preserves the doctype, if any, unchanged
        inject_meta_charset=True|False
          ..?
        lang_attr='preserve'|'xml'|'html'
          Whether to translate 'lang' attributes.
            * lang_attr='preserve' does no translation
            * lang_attr='xml' translates 'lang' to 'xml:lang'
            * lang_attr='html' translates 'xml:lang' to 'lang'
        quote_attr_values=True|False
          Whether to quote attribute values that don't require quoting
          per HTML5 parsing rules.
        quote_char=u'"'|u"'"
          Use given quote character for attribute quoting. Default is to
          use double quote unless attribute value contains a double quote,
          in which case single quotes are used instead.
        escape_lt_in_attrs=False|True
          Whether to escape < in attribute values.
        escape_rc_data=False|True
          ..?
        resolve_entities=True|False
          Whether to resolve named character entities that appear in the
          source tree. The XML predified entities &lt; &gt; &amp; &quot; &apos;
          are unaffected by this setting.
        strip_whitespace=False|True
          ..?
        minimize_boolean_attributes=True|false
          Shortens boolean attributes to give just the attribute value,
          for example <input disabled="disabled"> becomes <input disabled>.
        use_trailing_solidus
          Includes a close-tag slash at the end of the start tag of void
          elements (empty elements whose end tag is forbidden). E.g. <hr/>.
        space_before_trailing_solidus
          Places a space immediately before the closing slash in a tag
          using a trailing solidus. E.g. <hr />. Requires use_trailing_solidus.
        sanitize
          Strip all unsafe or unknown constructs from output.
          See `html5lib user documentation`_

        .. _html5lib user documentation: http://code.google.com/p/html5lib/wiki/UserDocumentation
        """
        if kwargs.has_key('quote_char'):
            self.use_best_quote_char = False
        for attr in self.options:
            setattr(self, attr, kwargs.get(attr, getattr(self, attr)))
        self.errors = []
        self.strict = False

    def calc_doctype(self, token=None):
        if self.emit_doctype == 'html5' or \
           not token and self.emit_doctype == 'html':
            if token:
                return u'<!DOCTYPE html>'
            else:
                return u'<!DOCTYPE html>\n'

        rootElement = token["name"]
        publicID    = token["publicId"]
        systemID    = token["systemId"]

        if re.match(u'html', rootElement, re.IGNORECASE):
            if self.emit_doctype == u'html':
                # XHTML 1.1
                if publicID == u"-//W3C//DTD XHTML 1.1//EN" and (not systemID \
                or systemID == u"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"):
                    publicID = u"-//W3C//DTD HTML 4.01//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/html4/strict.dtd"
                # XHTML 1.0 Strict
                elif publicID == u"-//W3C//DTD XHTML 1.0 Strict//EN" and (not systemID \
                or systemID == u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"):
                    publicID = u"-//W3C//DTD HTML 4.01//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/html4/strict.dtd"
                # XHTML 1.0 Transitional
                elif publicID == u"-//W3C//DTD XHTML 1.0 Transitional//EN" and (not systemID \
                or systemID == u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"):
                    publicID = u"-//W3C//DTD HTML 4.01 Transitional//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/html4/loose.dtd"
                # XHTML 1.0 Frameset
                elif publicID == u"-//W3C//DTD XHTML 1.0 Frameset//EN" and (not systemID \
                or systemID == u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd"):
                    publicID = u"-//W3C//DTD HTML 4.01 Frameset//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/html4/frameset.dtd"
            elif self.emit_doctype == u'xhtml':
                # HTML 4.01 Strict
                if re.match(u"-//W3C//DTD HTML 4.0(1)?//EN", publicID) and \
                (not systemID or \
                re.match(u"http://www.w3.org/TR/(html4|REC-html40)/strict.dtd", systemID)):
                    publicID = u"-//W3C//DTD XHTML 1.0 Strict//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
                # HTML4.01 Transitional
                elif re.match(u"-//W3C//DTD HTML 4.0(1)? Transitional//EN", publicID) and \
                (not systemID or \
                 re.match(u"http://www.w3.org/TR/(html4|REC-html40)/loose.dtd", systemID)):
                    publicID = u"-//W3C//DTD XHTML 1.0 Transitional//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
                # HTML 4.01 Frameset
                elif re.match(u"-//W3C//DTD HTML 4.0(1)? Frameset//EN", publicID) and \
                (not systemID or \
                 re.match(u"http://www.w3.org/TR/(html4|REC-html40)/frameset.dtd", systemID)):
                    publicID = u"-//W3C//DTD XHTML 1.0 Frameset//EN"
                    if systemID:
                        systemID = u"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd"
                # HTML 3.2
                elif re.match(u"-//W3C//DTD HTML 3.2( Final)?//EN", publicID) and not systemID:
                    publicID = u"-//W3C//DTD XHTML 1.0 Transitional//EN"

        doctype = u"<!DOCTYPE %s" % rootElement
        if token["publicId"]:
            doctype += u' PUBLIC "%s"' % publicID
        elif systemID:
            doctype += u" SYSTEM"
        if systemID:
            if systemID.find(u'"') >= 0:
                if systemID.find(u"'") >= 0:
                    self.serializeError(_("System identifer contains both single and double quote characters"))
                quote_char = u"'"
            else:
                quote_char = u'"'
            doctype += u" %s%s%s" % (quote_char, systemID, quote_char)
        doctype += u">"
        return doctype

    def serialize(self, treewalker, encoding=None):
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
        posted_doctype = False
        for token in treewalker:
            type = token["type"]
            if type == "Doctype":
                posted_doctype = True
                doctype = self.calc_doctype(token)
                if encoding:
                    yield doctype.encode(encoding)
                else:
                    yield doctype

            elif type in ("Characters", "SpaceCharacters"):
                if type == "SpaceCharacters" or in_cdata:
                    if in_cdata and token["data"].find("</") >= 0:
                        self.serializeError(_("Unexpected </ in CDATA"))
                    if encoding:
                        yield token["data"].encode(encoding, "strict")
                    else:
                        yield token["data"]
                elif encoding:
                    yield encode(escape(token["data"]), encoding)
                else:
                    yield escape(token["data"])

            elif type in ("StartTag", "EmptyTag"):
                if not posted_doctype:
                    posted_doctype = True
                    yield self.calc_doctype()
                name = token["name"]
                if name in rcdataElements and not self.escape_rcdata:
                    in_cdata = True
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                attrs = token["data"]
                if hasattr(attrs, "items"):
                    attrs = attrs.items()
                attributes = []
                for k,v in attrs:

                    # clean up xml:lang
                    if k == '{http://www.w3.org/XML/1998/namespace}lang':
                        k = 'xml:lang'
                    if self.lang_attr == 'xml':
                        if k == 'lang' and not ('xml:lang' in attrs or
                           '{http://www.w3.org/XML/1998/namespace}lang' in attrs):
                            k = 'xml:lang'
                    elif self.lang_attr == 'html':
                        if k == 'xml:lang' and not ('lang' in attrs):
                            k = 'lang'

                    if encoding:
                        k = k.encode(encoding, "strict")
                    attributes.append(' ')

                    attributes.append(k)
                    if not self.minimize_boolean_attributes or \
                      (k not in booleanAttributes.get(name, tuple()) \
                      and k not in booleanAttributes.get("", tuple())):
                        attributes.append("=")
                        if self.quote_attr_values or not v:
                            quote_attr = True
                        else:
                            quote_attr = reduce(lambda x,y: x or (y in v),
                                spaceCharacters + ">\"'=", False)
                        v = v.replace("&", "&amp;")
                        if self.escape_lt_in_attrs: v = v.replace("<", "&lt;")
                        if encoding:
                            v = encode(v, encoding)
                        if quote_attr:
                            quote_char = self.quote_char
                            if self.use_best_quote_char:
                                if "'" in v and '"' not in v:
                                    quote_char = '"'
                                elif '"' in v and "'" not in v:
                                    quote_char = "'"
                            if quote_char == "'":
                                v = v.replace("'", "&#39;")
                            else:
                                v = v.replace('"', "&quot;")
                            attributes.append(quote_char)
                            attributes.append(v)
                            attributes.append(quote_char)
                        else:
                            attributes.append(v)
                if name in voidElements and self.use_trailing_solidus:
                    if self.space_before_trailing_solidus:
                        attributes.append(" /")
                    else:
                        attributes.append("/")
                if encoding:
                    yield "<%s%s>" % (name.encode(encoding, "strict"), "".join(attributes))
                else:
                    yield u"<%s%s>" % (name, u"".join(attributes))

            elif type == "EndTag":
                name = token["name"]
                if name in rcdataElements:
                    in_cdata = False
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                end_tag = u"</%s>" % name
                if encoding:
                    end_tag = end_tag.encode(encoding, "strict")
                yield end_tag

            elif type == "Comment":
                data = token["data"]
                if data.find("--") >= 0:
                    self.serializeError(_("Comment contains --"))
                comment = u"<!--%s-->" % token["data"]
                if encoding:
                    comment = comment.encode(encoding, unicode_encode_errors)
                yield comment

            elif type == "Entity":
                name = token["name"]
                key = name + ";"
                if not key in entities:
                    self.serializeError(_("Entity %s not recognized" % name))
                if self.resolve_entities and key not in xmlEntities:
                    data = entities[key]
                else:
                    data = u"&%s;" % name
                if encoding:
                    data = data.encode(encoding, unicode_encode_errors)
                yield data

            else:
                self.serializeError(token["data"])

    def render(self, treewalker, encoding=None):
        if encoding:
            return "".join(list(self.serialize(treewalker, encoding)))
        else:
            return u"".join(list(self.serialize(treewalker)))

    def serializeError(self, data="XXX ERROR MESSAGE NEEDED"):
        # XXX The idea is to make data mandatory.
        self.errors.append(data)
        if self.strict:
            raise SerializeError

def SerializeError(Exception):
    """Error in serialized tree"""
    pass
