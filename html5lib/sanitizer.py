from __future__ import absolute_import
import re
from xml.sax.saxutils import escape, unescape

from .tokenizer import HTMLTokenizer
from .constants import tokenTypes

class HTMLSanitizerMixin(object):
    u""" sanitization of XHTML+MathML+SVG and of inline style attributes."""

    acceptable_elements = [u'a', u'abbr', u'acronym', u'address', u'area',
        u'article', u'aside', u'audio', u'b', u'big', u'blockquote', u'br', u'button',
        u'canvas', u'caption', u'center', u'cite', u'code', u'col', u'colgroup',
        u'command', u'datagrid', u'datalist', u'dd', u'del', u'details', u'dfn',
        u'dialog', u'dir', u'div', u'dl', u'dt', u'em', u'event-source', u'fieldset',
        u'figcaption', u'figure', u'footer', u'font', u'form', u'header', u'h1',
        u'h2', u'h3', u'h4', u'h5', u'h6', u'hr', u'i', u'img', u'input', u'ins',
        u'keygen', u'kbd', u'label', u'legend', u'li', u'm', u'map', u'menu', u'meter',
        u'multicol', u'nav', u'nextid', u'ol', u'output', u'optgroup', u'option',
        u'p', u'pre', u'progress', u'q', u's', u'samp', u'section', u'select',
        u'small', u'sound', u'source', u'spacer', u'span', u'strike', u'strong',
        u'sub', u'sup', u'table', u'tbody', u'td', u'textarea', u'time', u'tfoot',
        u'th', u'thead', u'tr', u'tt', u'u', u'ul', u'var', u'video']
      
    mathml_elements = [u'maction', u'math', u'merror', u'mfrac', u'mi',
        u'mmultiscripts', u'mn', u'mo', u'mover', u'mpadded', u'mphantom',
        u'mprescripts', u'mroot', u'mrow', u'mspace', u'msqrt', u'mstyle', u'msub',
        u'msubsup', u'msup', u'mtable', u'mtd', u'mtext', u'mtr', u'munder',
        u'munderover', u'none']
      
    svg_elements = [u'a', u'animate', u'animateColor', u'animateMotion',
        u'animateTransform', u'clipPath', u'circle', u'defs', u'desc', u'ellipse',
        u'font-face', u'font-face-name', u'font-face-src', u'g', u'glyph', u'hkern',
        u'linearGradient', u'line', u'marker', u'metadata', u'missing-glyph',
        u'mpath', u'path', u'polygon', u'polyline', u'radialGradient', u'rect',
        u'set', u'stop', u'svg', u'switch', u'text', u'title', u'tspan', u'use']
        
    acceptable_attributes = [u'abbr', u'accept', u'accept-charset', u'accesskey',
        u'action', u'align', u'alt', u'autocomplete', u'autofocus', u'axis',
        u'background', u'balance', u'bgcolor', u'bgproperties', u'border',
        u'bordercolor', u'bordercolordark', u'bordercolorlight', u'bottompadding',
        u'cellpadding', u'cellspacing', u'ch', u'challenge', u'char', u'charoff',
        u'choff', u'charset', u'checked', u'cite', u'class', u'clear', u'color',
        u'cols', u'colspan', u'compact', u'contenteditable', u'controls', u'coords',
        u'data', u'datafld', u'datapagesize', u'datasrc', u'datetime', u'default',
        u'delay', u'dir', u'disabled', u'draggable', u'dynsrc', u'enctype', u'end',
        u'face', u'for', u'form', u'frame', u'galleryimg', u'gutter', u'headers',
        u'height', u'hidefocus', u'hidden', u'high', u'href', u'hreflang', u'hspace',
        u'icon', u'id', u'inputmode', u'ismap', u'keytype', u'label', u'leftspacing',
        u'lang', u'list', u'longdesc', u'loop', u'loopcount', u'loopend',
        u'loopstart', u'low', u'lowsrc', u'max', u'maxlength', u'media', u'method',
        u'min', u'multiple', u'name', u'nohref', u'noshade', u'nowrap', u'open',
        u'optimum', u'pattern', u'ping', u'point-size', u'poster', u'pqg', u'preload',
        u'prompt', u'radiogroup', u'readonly', u'rel', u'repeat-max', u'repeat-min',
        u'replace', u'required', u'rev', u'rightspacing', u'rows', u'rowspan',
        u'rules', u'scope', u'selected', u'shape', u'size', u'span', u'src', u'start',
        u'step', u'style', u'summary', u'suppress', u'tabindex', u'target',
        u'template', u'title', u'toppadding', u'type', u'unselectable', u'usemap',
        u'urn', u'valign', u'value', u'variable', u'volume', u'vspace', u'vrml',
        u'width', u'wrap', u'xml:lang']

    mathml_attributes = [u'actiontype', u'align', u'columnalign', u'columnalign',
        u'columnalign', u'columnlines', u'columnspacing', u'columnspan', u'depth',
        u'display', u'displaystyle', u'equalcolumns', u'equalrows', u'fence',
        u'fontstyle', u'fontweight', u'frame', u'height', u'linethickness', u'lspace',
        u'mathbackground', u'mathcolor', u'mathvariant', u'mathvariant', u'maxsize',
        u'minsize', u'other', u'rowalign', u'rowalign', u'rowalign', u'rowlines',
        u'rowspacing', u'rowspan', u'rspace', u'scriptlevel', u'selection',
        u'separator', u'stretchy', u'width', u'width', u'xlink:href', u'xlink:show',
        u'xlink:type', u'xmlns', u'xmlns:xlink']
  
    svg_attributes = [u'accent-height', u'accumulate', u'additive', u'alphabetic',
        u'arabic-form', u'ascent', u'attributeName', u'attributeType',
        u'baseProfile', u'bbox', u'begin', u'by', u'calcMode', u'cap-height',
        u'class', u'clip-path', u'color', u'color-rendering', u'content', u'cx',
        u'cy', u'd', u'dx', u'dy', u'descent', u'display', u'dur', u'end', u'fill',
        u'fill-opacity', u'fill-rule', u'font-family', u'font-size',
        u'font-stretch', u'font-style', u'font-variant', u'font-weight', u'from',
        u'fx', u'fy', u'g1', u'g2', u'glyph-name', u'gradientUnits', u'hanging',
        u'height', u'horiz-adv-x', u'horiz-origin-x', u'id', u'ideographic', u'k',
        u'keyPoints', u'keySplines', u'keyTimes', u'lang', u'marker-end',
        u'marker-mid', u'marker-start', u'markerHeight', u'markerUnits',
        u'markerWidth', u'mathematical', u'max', u'min', u'name', u'offset',
        u'opacity', u'orient', u'origin', u'overline-position',
        u'overline-thickness', u'panose-1', u'path', u'pathLength', u'points',
        u'preserveAspectRatio', u'r', u'refX', u'refY', u'repeatCount',
        u'repeatDur', u'requiredExtensions', u'requiredFeatures', u'restart',
        u'rotate', u'rx', u'ry', u'slope', u'stemh', u'stemv', u'stop-color',
        u'stop-opacity', u'strikethrough-position', u'strikethrough-thickness',
        u'stroke', u'stroke-dasharray', u'stroke-dashoffset', u'stroke-linecap',
        u'stroke-linejoin', u'stroke-miterlimit', u'stroke-opacity',
        u'stroke-width', u'systemLanguage', u'target', u'text-anchor', u'to',
        u'transform', u'type', u'u1', u'u2', u'underline-position',
        u'underline-thickness', u'unicode', u'unicode-range', u'units-per-em',
        u'values', u'version', u'viewBox', u'visibility', u'width', u'widths', u'x',
        u'x-height', u'x1', u'x2', u'xlink:actuate', u'xlink:arcrole',
        u'xlink:href', u'xlink:role', u'xlink:show', u'xlink:title', u'xlink:type',
        u'xml:base', u'xml:lang', u'xml:space', u'xmlns', u'xmlns:xlink', u'y',
        u'y1', u'y2', u'zoomAndPan']

    attr_val_is_uri = [u'href', u'src', u'cite', u'action', u'longdesc', u'poster',
        u'xlink:href', u'xml:base']

    svg_attr_val_allows_ref = [u'clip-path', u'color-profile', u'cursor', u'fill',
        u'filter', u'marker', u'marker-start', u'marker-mid', u'marker-end',
        u'mask', u'stroke']

    svg_allow_local_href = [u'altGlyph', u'animate', u'animateColor',
        u'animateMotion', u'animateTransform', u'cursor', u'feImage', u'filter',
        u'linearGradient', u'pattern', u'radialGradient', u'textpath', u'tref',
        u'set', u'use']
  
    acceptable_css_properties = [u'azimuth', u'background-color',
        u'border-bottom-color', u'border-collapse', u'border-color',
        u'border-left-color', u'border-right-color', u'border-top-color', u'clear',
        u'color', u'cursor', u'direction', u'display', u'elevation', u'float', u'font',
        u'font-family', u'font-size', u'font-style', u'font-variant', u'font-weight',
        u'height', u'letter-spacing', u'line-height', u'overflow', u'pause',
        u'pause-after', u'pause-before', u'pitch', u'pitch-range', u'richness',
        u'speak', u'speak-header', u'speak-numeral', u'speak-punctuation',
        u'speech-rate', u'stress', u'text-align', u'text-decoration', u'text-indent',
        u'unicode-bidi', u'vertical-align', u'voice-family', u'volume',
        u'white-space', u'width']
  
    acceptable_css_keywords = [u'auto', u'aqua', u'black', u'block', u'blue',
        u'bold', u'both', u'bottom', u'brown', u'center', u'collapse', u'dashed',
        u'dotted', u'fuchsia', u'gray', u'green', u'!important', u'italic', u'left',
        u'lime', u'maroon', u'medium', u'none', u'navy', u'normal', u'nowrap', u'olive',
        u'pointer', u'purple', u'red', u'right', u'solid', u'silver', u'teal', u'top',
        u'transparent', u'underline', u'white', u'yellow']
  
    acceptable_svg_properties = [ u'fill', u'fill-opacity', u'fill-rule',
        u'stroke', u'stroke-width', u'stroke-linecap', u'stroke-linejoin',
        u'stroke-opacity']
  
    acceptable_protocols = [ u'ed2k', u'ftp', u'http', u'https', u'irc',
        u'mailto', u'news', u'gopher', u'nntp', u'telnet', u'webcal',
        u'xmpp', u'callto', u'feed', u'urn', u'aim', u'rsync', u'tag',
        u'ssh', u'sftp', u'rtsp', u'afs' ]
  
    # subclasses may define their own versions of these constants
    allowed_elements = acceptable_elements + mathml_elements + svg_elements
    allowed_attributes = acceptable_attributes + mathml_attributes + svg_attributes
    allowed_css_properties = acceptable_css_properties
    allowed_css_keywords = acceptable_css_keywords
    allowed_svg_properties = acceptable_svg_properties
    allowed_protocols = acceptable_protocols

    # Sanitize the +html+, escaping all elements not in ALLOWED_ELEMENTS, and
    # stripping out all # attributes not in ALLOWED_ATTRIBUTES. Style
    # attributes are parsed, and a restricted set, # specified by
    # ALLOWED_CSS_PROPERTIES and ALLOWED_CSS_KEYWORDS, are allowed through.
    # attributes in ATTR_VAL_IS_URI are scanned, and only URI schemes specified
    # in ALLOWED_PROTOCOLS are allowed.
    #
    #   sanitize_html('<script> do_nasty_stuff() </script>')
    #    => &lt;script> do_nasty_stuff() &lt;/script>
    #   sanitize_html('<a href="javascript: sucker();">Click here for $100</a>')
    #    => <a>Click here for $100</a>
    def sanitize_token(self, token):

        # accommodate filters which use token_type differently
        token_type = token[u"type"]
        if token_type in list(tokenTypes.keys()):
          token_type = tokenTypes[token_type]

        if token_type in (tokenTypes[u"StartTag"], tokenTypes[u"EndTag"], 
                             tokenTypes[u"EmptyTag"]):
            if token[u"name"] in self.allowed_elements:
                if u"data" in token:
                    attrs = dict([(name,val) for name,val in
                                  token[u"data"][::-1] 
                                  if name in self.allowed_attributes])
                    for attr in self.attr_val_is_uri:
                        if attr not in attrs:
                            continue
                        val_unescaped = re.sub(u"[`\000-\040\177-\240\s]+", u'',
                                               unescape(attrs[attr])).lower()
                        #remove replacement characters from unescaped characters
                        val_unescaped = val_unescaped.replace(u"\ufffd", u"")
                        if (re.match(u"^[a-z0-9][-+.a-z0-9]*:",val_unescaped) and
                            (val_unescaped.split(u':')[0] not in 
                             self.allowed_protocols)):
                            del attrs[attr]
                    for attr in self.svg_attr_val_allows_ref:
                        if attr in attrs:
                            attrs[attr] = re.sub(ur'url\s*\(\s*[^#\s][^)]+?\)',
                                                 u' ',
                                                 unescape(attrs[attr]))
                    if (token[u"name"] in self.svg_allow_local_href and
                        u'xlink:href' in attrs and re.search(u'^\s*[^#\s].*',
                                                            attrs[u'xlink:href'])):
                        del attrs[u'xlink:href']
                    if u'style' in attrs:
                        attrs[u'style'] = self.sanitize_css(attrs[u'style'])
                    token[u"data"] = [[name,val] for name,val in list(attrs.items())]
                return token
            else:
                if token_type == tokenTypes[u"EndTag"]:
                    token[u"data"] = u"</%s>" % token[u"name"]
                elif token[u"data"]:
                    attrs = u''.join([u' %s="%s"' % (k,escape(v)) for k,v in token[u"data"]])
                    token[u"data"] = u"<%s%s>" % (token[u"name"],attrs)
                else:
                    token[u"data"] = u"<%s>" % token[u"name"]
                if token.get(u"selfClosing"):
                    token[u"data"]=token[u"data"][:-1] + u"/>"

                if token[u"type"] in list(tokenTypes.keys()):
                    token[u"type"] = u"Characters"
                else:
                    token[u"type"] = tokenTypes[u"Characters"]

                del token[u"name"]
                return token
        elif token_type == tokenTypes[u"Comment"]:
            pass
        else:
            return token
    sanitize_token.func_annotations = {}

    def sanitize_css(self, style):
        # disallow urls
        style=re.compile(u'url\s*\(\s*[^\s)]+?\s*\)\s*').sub(u' ',style)

        # gauntlet
        if not re.match(u"""^([:,;#%.\sa-zA-Z0-9!]|\w-\w|'[\s\w]+'|"[\s\w]+"|\([\d,\s]+\))*$""", style): return u''
        if not re.match(u"^\s*([-\w]+\s*:[^:;]*(;\s*|$))*$", style): return u''

        clean = []
        for prop,value in re.findall(u"([-\w]+)\s*:\s*([^:;]*)",style):
          if not value: continue
          if prop.lower() in self.allowed_css_properties:
              clean.append(prop + u': ' + value + u';')
          elif prop.split(u'-')[0].lower() in [u'background',u'border',u'margin',
                                              u'padding']:
              for keyword in value.split():
                  if not keyword in self.acceptable_css_keywords and \
                      not re.match(u"^(#[0-9a-f]+|rgb\(\d+%?,\d*%?,?\d*%?\)?|\d{0,2}\.?\d{0,2}(cm|em|ex|in|mm|pc|pt|px|%|,|\))?)$",keyword):
                      break
              else:
                  clean.append(prop + u': ' + value + u';')
          elif prop.lower() in self.allowed_svg_properties:
              clean.append(prop + u': ' + value + u';')

        return u' '.join(clean)
    sanitize_css.func_annotations = {}

class HTMLSanitizer(HTMLTokenizer, HTMLSanitizerMixin):
    def __init__(self, stream, encoding=None, parseMeta=True, useChardet=True,
                 lowercaseElementName=False, lowercaseAttrName=False, parser=None):
        #Change case matching defaults as we only output lowercase html anyway
        #This solution doesn't seem ideal...
        HTMLTokenizer.__init__(self, stream, encoding, parseMeta, useChardet,
                               lowercaseElementName, lowercaseAttrName, parser=parser)
    __init__.func_annotations = {}

    def __iter__(self):
        for token in HTMLTokenizer.__iter__(self):
            token = self.sanitize_token(token)
            if token:
                yield token
    __iter__.func_annotations = {}
