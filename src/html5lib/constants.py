import string, gettext
_ = gettext.gettext

EOF = None

E = {
    "null-character": 
       _("Null character in input stream, replaced with U+FFFD."),
    "invalid-character": 
       _("Invalid codepoint in stream."),
    "incorrectly-placed-solidus":
       _("Solidus (/) incorrectly placed in tag."),
    "incorrect-cr-newline-entity":
       _("Incorrect CR newline entity, replaced with LF."),
    "illegal-windows-1252-entity":
       _("Entity used with illegal number (windows-1252 reference)."),
    "cant-convert-numeric-entity":
       _("Numeric entity couldn't be converted to character "
         "(codepoint U+%(charAsInt)08x)."),
    "illegal-codepoint-for-numeric-entity":
       _("Numeric entity represents an illegal codepoint: "
         "U+%(charAsInt)08x."),
    "numeric-entity-without-semicolon":
       _("Numeric entity didn't end with ';'."),
    "expected-numeric-entity-but-got-eof":
       _("Numeric entity expected. Got end of file instead."),
    "expected-numeric-entity":
       _("Numeric entity expected but none found."),
    "named-entity-without-semicolon":
       _("Named entity didn't end with ';'."),
    "expected-named-entity":
       _("Named entity expected. Got none."),
    "attributes-in-end-tag":
       _("End tag contains unexpected attributes."),
    "expected-tag-name-but-got-right-bracket":
       _("Expected tag name. Got '>' instead."),
    "expected-tag-name-but-got-question-mark":
       _("Expected tag name. Got '?' instead. (HTML doesn't "
         "support processing instructions.)"),
    "expected-tag-name":
       _("Expected tag name. Got something else instead"),
    "expected-closing-tag-but-got-right-bracket":
       _("Expected closing tag. Got '>' instead. Ignoring '</>'."),
    "expected-closing-tag-but-got-eof":
       _("Expected closing tag. Unexpected end of file."),
    "expected-closing-tag-but-got-char":
       _("Expected closing tag. Unexpected character '%(data)s' found."),
    "eof-in-tag-name":
       _("Unexpected end of file in the tag name."),
    "expected-attribute-name-but-got-eof":
       _("Unexpected end of file. Expected attribute name instead."),
    "eof-in-attribute-name":
       _("Unexpected end of file in attribute name."),
    "duplicate-attribute":
       _("Dropped duplicate attribute on tag."),
    "expected-end-of-tag-name-but-got-eof":
       _("Unexpected end of file. Expected = or end of tag."),
    "expected-attribute-value-but-got-eof":
       _("Unexpected end of file. Expected attribute value."),
    "expected-attribute-value-but-got-right-bracket":
       _("Expected attribute value. Got '>' instead."),
    "eof-in-attribute-value-double-quote":
       _("Unexpected end of file in attribute value (\")."),
    "eof-in-attribute-value-single-quote":
       _("Unexpected end of file in attribute value (')."),
    "eof-in-attribute-value-no-quotes":
       _("Unexpected end of file in attribute value."),
    "unexpected-EOF-after-solidus-in-tag":
        _("Unexpected end of file in tag. Expected >"),
    "unexpected-character-after-soldius-in-tag":
        _("Unexpected character after / in tag. Expected >"),
    "expected-dashes-or-doctype":
       _("Expected '--' or 'DOCTYPE'. Not found."),
    "incorrect-comment":
       _("Incorrect comment."),
    "eof-in-comment":
       _("Unexpected end of file in comment."),
    "eof-in-comment-end-dash":
       _("Unexpected end of file in comment (-)"),
    "unexpected-dash-after-double-dash-in-comment":
       _("Unexpected '-' after '--' found in comment."),
    "eof-in-comment-double-dash":
       _("Unexpected end of file in comment (--)."),
    "unexpected-char-in-comment":
       _("Unexpected character in comment found."),
    "need-space-after-doctype":
       _("No space after literal string 'DOCTYPE'."),
    "expected-doctype-name-but-got-right-bracket":
       _("Unexpected > character. Expected DOCTYPE name."),
    "expected-doctype-name-but-got-eof":
       _("Unexpected end of file. Expected DOCTYPE name."),
    "eof-in-doctype-name":
       _("Unexpected end of file in DOCTYPE name."),
    "eof-in-doctype":
       _("Unexpected end of file in DOCTYPE."),
    "expected-space-or-right-bracket-in-doctype":
       _("Expected space or '>'. Got '%(data)s'"),
    "unexpected-end-of-doctype":
       _("Unexpected end of DOCTYPE."),
    "unexpected-char-in-doctype":
       _("Unexpected character in DOCTYPE."),
    "eof-in-innerhtml":
       _("XXX innerHTML EOF"),
    "unexpected-doctype":
       _("Unexpected DOCTYPE. Ignored."),
    "non-html-root":
       _("html needs to be the first start tag."),
    "expected-doctype-but-got-eof":
       _("Unexpected End of file. Expected DOCTYPE."),
    "unknown-doctype":
       _("Erroneous DOCTYPE."),
    "expected-doctype-but-got-chars":
       _("Unexpected non-space characters. Expected DOCTYPE."),
    "expected-doctype-but-got-start-tag":
       _("Unexpected start tag (%(name)s). Expected DOCTYPE."),
    "expected-doctype-but-got-end-tag":
       _("Unexpected end tag (%(name)s). Expected DOCTYPE."),
    "end-tag-after-implied-root":
       _("Unexpected end tag (%(name)s) after the (implied) root element."),
    "expected-named-closing-tag-but-got-eof":
       _("Unexpected end of file. Expected end tag (%(name)s)."),
    "two-heads-are-not-better-than-one":
       _("Unexpected start tag head in existing head. Ignored."),
    "unexpected-end-tag":
       _("Unexpected end tag (%(name)s). Ignored."),
    "unexpected-start-tag-out-of-my-head":
       _("Unexpected start tag (%(name)s) that can be in head. Moved."),
    "unexpected-start-tag":
       _("Unexpected start tag (%(name)s)."),
    "missing-end-tag":
       _("Missing end tag (%(name)s)."),
    "missing-end-tags":
       _("Missing end tags (%(name)s)."),
    "unexpected-start-tag-implies-end-tag":
       _("Unexpected start tag (%(startName)s) "
         "implies end tag (%(endName)s)."),
    "unexpected-start-tag-treated-as":
       _("Unexpected start tag (%(originalName)s). Treated as %(newName)s."),
    "deprecated-tag":
       _("Unexpected start tag %(name)s. Don't use it!"),
    "unexpected-start-tag-ignored":
       _("Unexpected start tag %(name)s. Ignored."),
    "expected-one-end-tag-but-got-another":
       _("Unexpected end tag (%(gotName)s). "
         "Missing end tag (%(expectedName)s)."),
    "end-tag-too-early":
       _("End tag (%(name)s) seen too early. Expected other end tag."),
    "end-tag-too-early-named":
       _("Unexpected end tag (%(gotName)s). Expected end tag (%(expectedName)s)."),
    "end-tag-too-early-ignored":
       _("End tag (%(name)s) seen too early. Ignored."),
    "adoption-agency-1.1":
       _("End tag (%(name)s) violates step 1, "
         "paragraph 1 of the adoption agency algorithm."),
    "adoption-agency-1.2":
       _("End tag (%(name)s) violates step 1, "
         "paragraph 2 of the adoption agency algorithm."),
    "adoption-agency-1.3":
       _("End tag (%(name)s) violates step 1, "
         "paragraph 3 of the adoption agency algorithm."),
    "unexpected-end-tag-treated-as":
       _("Unexpected end tag (%(originalName)s). Treated as %(newName)s."),
    "no-end-tag":
       _("This element (%(name)s) has no end tag."),
    "unexpected-implied-end-tag-in-table":
       _("Unexpected implied end tag (%(name)s) in the table phase."),
    "unexpected-implied-end-tag-in-table-body":
       _("Unexpected implied end tag (%(name)s) in the table body phase."),
    "unexpected-char-implies-table-voodoo":
       _("Unexpected non-space characters in "
         "table context caused voodoo mode."),
    "unexpected-hidden-input-in-table":
       _("Unexpected input with type hidden in table context."),
    "unexpected-start-tag-implies-table-voodoo":
       _("Unexpected start tag (%(name)s) in "
         "table context caused voodoo mode."),
    "unexpected-end-tag-implies-table-voodoo":
       _("Unexpected end tag (%(name)s) in "
         "table context caused voodoo mode."),
    "unexpected-cell-in-table-body":
       _("Unexpected table cell start tag (%(name)s) "
         "in the table body phase."),
    "unexpected-cell-end-tag":
       _("Got table cell end tag (%(name)s) "
         "while required end tags are missing."),
    "unexpected-end-tag-in-table-body":
       _("Unexpected end tag (%(name)s) in the table body phase. Ignored."),
    "unexpected-implied-end-tag-in-table-row":
       _("Unexpected implied end tag (%(name)s) in the table row phase."),
    "unexpected-end-tag-in-table-row":
       _("Unexpected end tag (%(name)s) in the table row phase. Ignored."),
    "unexpected-select-in-select":
       _("Unexpected select start tag in the select phase "
         "treated as select end tag."),
    "unexpected-input-in-select":
       _("Unexpected input start tag in the select phase."),
    "unexpected-start-tag-in-select":
       _("Unexpected start tag token (%(name)s in the select phase. "
         "Ignored."),
    "unexpected-end-tag-in-select":
       _("Unexpected end tag (%(name)s) in the select phase. Ignored."),
    "unexpected-table-element-start-tag-in-select-in-table":
       _("Unexpected table element start tag (%(name)s) in the select in table phase."),
    "unexpected-table-element-end-tag-in-select-in-table":
       _("Unexpected table element end tag (%(name)s) in the select in table phase."),
    "unexpected-char-after-body":
       _("Unexpected non-space characters in the after body phase."),
    "unexpected-start-tag-after-body":
       _("Unexpected start tag token (%(name)s)"
         " in the after body phase."),
    "unexpected-end-tag-after-body":
       _("Unexpected end tag token (%(name)s)"
         " in the after body phase."),
    "unexpected-char-in-frameset":
       _("Unepxected characters in the frameset phase. Characters ignored."),
    "unexpected-start-tag-in-frameset":
       _("Unexpected start tag token (%(name)s)"
         " in the frameset phase. Ignored."),
    "unexpected-frameset-in-frameset-innerhtml":
       _("Unexpected end tag token (frameset) "
         "in the frameset phase (innerHTML)."),
    "unexpected-end-tag-in-frameset":
       _("Unexpected end tag token (%(name)s)"
         " in the frameset phase. Ignored."),
    "unexpected-char-after-frameset":
       _("Unexpected non-space characters in the "
         "after frameset phase. Ignored."),
    "unexpected-start-tag-after-frameset":
       _("Unexpected start tag (%(name)s)"
         " in the after frameset phase. Ignored."),
    "unexpected-end-tag-after-frameset":
       _("Unexpected end tag (%(name)s)"
         " in the after frameset phase. Ignored."),
    "unexpected-end-tag-after-body-innerhtml":
       _("Unexpected end tag after body(innerHtml)"),
    "expected-eof-but-got-char":
       _("Unexpected non-space characters. Expected end of file."),
    "expected-eof-but-got-start-tag":
       _("Unexpected start tag (%(name)s)"
         ". Expected end of file."),
    "expected-eof-but-got-end-tag":
       _("Unexpected end tag (%(name)s)"
         ". Expected end of file."),
    "eof-in-table":
       _("Unexpected end of file. Expected table content."),
    "eof-in-select":
       _("Unexpected end of file. Expected select content."),
    "eof-in-frameset":
       _("Unexpected end of file. Expected frameset content."),
    "XXX-undefined-error":
        ("Undefined error (this sucks and should be fixed)"),
}

contentModelFlags = {
    "PCDATA":0,
    "RCDATA":1,
    "CDATA":2,
    "PLAINTEXT":3
}

scopingElements = frozenset((
    "applet",
    "button",
    "caption",
    "html",
    "marquee",
    "object",
    "table",
    "td",
    "th"
))

formattingElements = frozenset((
    "a",
    "b",
    "big",
    "em",
    "font",
    "i",
    "nobr",
    "s",
    "small",
    "strike",
    "strong",
    "tt",
    "u"
))

specialElements = frozenset((
    "address",
    "area",
    "article",
    "aside",
    "base",
    "basefont",
    "bgsound",
    "blockquote",
    "body",
    "br",
    "center",
    "col",
    "colgroup",
    "command",
    "datagrid",
    "dd",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "dt",
    "embed",
    "event-source",
    "fieldset",
    "figure",
    "footer",
    "form",
    "frame",
    "frameset",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hr",
    "iframe",
    # Note that image is commented out in the spec as "this isn't an
    # element that can end up on the stack, so it doesn't matter"
    "image", 
    "img",
    "input",
    "isindex",
    "li",
    "link",
    "listing",
    "menu",
    "meta",
    "nav",
    "noembed",
    "noframes",
    "noscript",
    "ol",
    "optgroup",
    "option",
    "p",
    "param",
    "plaintext",
    "pre",
    "script",
    "section",
    "select",
    "spacer",
    "style",
    "tbody",
    "textarea",
    "tfoot",
    "thead",
    "title",
    "tr",
    "ul",
    "wbr"
))

spaceCharacters = frozenset((
    "\t",
    "\n",
    "\u000C",
    " ",
    "\r"
))

tableInsertModeElements = frozenset((
    "table",
    "tbody",
    "tfoot",
    "thead",
    "tr"
))

asciiLowercase = frozenset(string.ascii_lowercase)
asciiUppercase = frozenset(string.ascii_uppercase)
asciiLetters = frozenset(string.ascii_letters)
digits = frozenset(string.digits)
hexDigits = frozenset(string.hexdigits)

asciiUpper2Lower = dict([(ord(c),ord(c.lower()))
    for c in string.ascii_uppercase])

# Heading elements need to be ordered
headingElements = (
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6"
)

voidElements = frozenset((
    "base",
    "command",
    "event-source",
    "link",
    "meta",
    "hr",
    "br",
    "img",
    "embed",
    "param",
    "area",
    "col",
    "input",
    "source"
))

cdataElements = frozenset(('title', 'textarea'))

rcdataElements = frozenset((
    'style',
    'script',
    'xmp',
    'iframe',
    'noembed',
    'noframes',
    'noscript'
))

booleanAttributes = {
    "": frozenset(("irrelevant",)),
    "style": frozenset(("scoped",)),
    "img": frozenset(("ismap",)),
    "audio": frozenset(("autoplay","controls")),
    "video": frozenset(("autoplay","controls")),
    "script": frozenset(("defer", "async")),
    "details": frozenset(("open",)),
    "datagrid": frozenset(("multiple", "disabled")),
    "command": frozenset(("hidden", "disabled", "checked", "default")),
    "menu": frozenset(("autosubmit",)),
    "fieldset": frozenset(("disabled", "readonly")),
    "option": frozenset(("disabled", "readonly", "selected")),
    "optgroup": frozenset(("disabled", "readonly")),
    "button": frozenset(("disabled", "autofocus")),
    "input": frozenset(("disabled", "readonly", "required", "autofocus", "checked", "ismap")),
    "select": frozenset(("disabled", "readonly", "autofocus", "multiple")),
    "output": frozenset(("disabled", "readonly")),
}

# entitiesWindows1252 has to be _ordered_ and needs to have an index. It
# therefore can't be a frozenset.
entitiesWindows1252 = (
    8364,  # 0x80  0x20AC  EURO SIGN
    65533, # 0x81          UNDEFINED
    8218,  # 0x82  0x201A  SINGLE LOW-9 QUOTATION MARK
    402,   # 0x83  0x0192  LATIN SMALL LETTER F WITH HOOK
    8222,  # 0x84  0x201E  DOUBLE LOW-9 QUOTATION MARK
    8230,  # 0x85  0x2026  HORIZONTAL ELLIPSIS
    8224,  # 0x86  0x2020  DAGGER
    8225,  # 0x87  0x2021  DOUBLE DAGGER
    710,   # 0x88  0x02C6  MODIFIER LETTER CIRCUMFLEX ACCENT
    8240,  # 0x89  0x2030  PER MILLE SIGN
    352,   # 0x8A  0x0160  LATIN CAPITAL LETTER S WITH CARON
    8249,  # 0x8B  0x2039  SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    338,   # 0x8C  0x0152  LATIN CAPITAL LIGATURE OE
    65533, # 0x8D          UNDEFINED
    381,   # 0x8E  0x017D  LATIN CAPITAL LETTER Z WITH CARON
    65533, # 0x8F          UNDEFINED
    65533, # 0x90          UNDEFINED
    8216,  # 0x91  0x2018  LEFT SINGLE QUOTATION MARK
    8217,  # 0x92  0x2019  RIGHT SINGLE QUOTATION MARK
    8220,  # 0x93  0x201C  LEFT DOUBLE QUOTATION MARK
    8221,  # 0x94  0x201D  RIGHT DOUBLE QUOTATION MARK
    8226,  # 0x95  0x2022  BULLET
    8211,  # 0x96  0x2013  EN DASH
    8212,  # 0x97  0x2014  EM DASH
    732,   # 0x98  0x02DC  SMALL TILDE
    8482,  # 0x99  0x2122  TRADE MARK SIGN
    353,   # 0x9A  0x0161  LATIN SMALL LETTER S WITH CARON
    8250,  # 0x9B  0x203A  SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    339,   # 0x9C  0x0153  LATIN SMALL LIGATURE OE
    65533, # 0x9D          UNDEFINED
    382,   # 0x9E  0x017E  LATIN SMALL LETTER Z WITH CARON
    376    # 0x9F  0x0178  LATIN CAPITAL LETTER Y WITH DIAERESIS
)

entities = {
    "AElig;": "\u00C6",
    "AElig": "\u00C6",
    "AMP;": "\u0026",
    "AMP": "\u0026",
    "Aacute;": "\u00C1",
    "Aacute": "\u00C1",
    "Acirc;": "\u00C2",
    "Acirc": "\u00C2",
    "Agrave;": "\u00C0",
    "Agrave": "\u00C0",
    "Alpha;": "\u0391",
    "Aring;": "\u00C5",
    "Aring": "\u00C5",
    "Atilde;": "\u00C3",
    "Atilde": "\u00C3",
    "Auml;": "\u00C4",
    "Auml": "\u00C4",
    "Beta;": "\u0392",
    "COPY;": "\u00A9",
    "COPY": "\u00A9",
    "Ccedil;": "\u00C7",
    "Ccedil": "\u00C7",
    "Chi;": "\u03A7",
    "Dagger;": "\u2021",
    "Delta;": "\u0394",
    "ETH;": "\u00D0",
    "ETH": "\u00D0",
    "Eacute;": "\u00C9",
    "Eacute": "\u00C9",
    "Ecirc;": "\u00CA",
    "Ecirc": "\u00CA",
    "Egrave;": "\u00C8",
    "Egrave": "\u00C8",
    "Epsilon;": "\u0395",
    "Eta;": "\u0397",
    "Euml;": "\u00CB",
    "Euml": "\u00CB",
    "GT;": "\u003E",
    "GT": "\u003E",
    "Gamma;": "\u0393",
    "Iacute;": "\u00CD",
    "Iacute": "\u00CD",
    "Icirc;": "\u00CE",
    "Icirc": "\u00CE",
    "Igrave;": "\u00CC",
    "Igrave": "\u00CC",
    "Iota;": "\u0399",
    "Iuml;": "\u00CF",
    "Iuml": "\u00CF",
    "Kappa;": "\u039A",
    "LT;": "\u003C",
    "LT": "\u003C",
    "Lambda;": "\u039B",
    "Mu;": "\u039C",
    "Ntilde;": "\u00D1",
    "Ntilde": "\u00D1",
    "Nu;": "\u039D",
    "OElig;": "\u0152",
    "Oacute;": "\u00D3",
    "Oacute": "\u00D3",
    "Ocirc;": "\u00D4",
    "Ocirc": "\u00D4",
    "Ograve;": "\u00D2",
    "Ograve": "\u00D2",
    "Omega;": "\u03A9",
    "Omicron;": "\u039F",
    "Oslash;": "\u00D8",
    "Oslash": "\u00D8",
    "Otilde;": "\u00D5",
    "Otilde": "\u00D5",
    "Ouml;": "\u00D6",
    "Ouml": "\u00D6",
    "Phi;": "\u03A6",
    "Pi;": "\u03A0",
    "Prime;": "\u2033",
    "Psi;": "\u03A8",
    "QUOT;": "\u0022",
    "QUOT": "\u0022",
    "REG;": "\u00AE",
    "REG": "\u00AE",
    "Rho;": "\u03A1",
    "Scaron;": "\u0160",
    "Sigma;": "\u03A3",
    "THORN;": "\u00DE",
    "THORN": "\u00DE",
    "TRADE;": "\u2122",
    "Tau;": "\u03A4",
    "Theta;": "\u0398",
    "Uacute;": "\u00DA",
    "Uacute": "\u00DA",
    "Ucirc;": "\u00DB",
    "Ucirc": "\u00DB",
    "Ugrave;": "\u00D9",
    "Ugrave": "\u00D9",
    "Upsilon;": "\u03A5",
    "Uuml;": "\u00DC",
    "Uuml": "\u00DC",
    "Xi;": "\u039E",
    "Yacute;": "\u00DD",
    "Yacute": "\u00DD",
    "Yuml;": "\u0178",
    "Zeta;": "\u0396",
    "aacute;": "\u00E1",
    "aacute": "\u00E1",
    "acirc;": "\u00E2",
    "acirc": "\u00E2",
    "acute;": "\u00B4",
    "acute": "\u00B4",
    "aelig;": "\u00E6",
    "aelig": "\u00E6",
    "agrave;": "\u00E0",
    "agrave": "\u00E0",
    "alefsym;": "\u2135",
    "alpha;": "\u03B1",
    "amp;": "\u0026",
    "amp": "\u0026",
    "and;": "\u2227",
    "ang;": "\u2220",
    "apos;": "\u0027",
    "aring;": "\u00E5",
    "aring": "\u00E5",
    "asymp;": "\u2248",
    "atilde;": "\u00E3",
    "atilde": "\u00E3",
    "auml;": "\u00E4",
    "auml": "\u00E4",
    "bdquo;": "\u201E",
    "beta;": "\u03B2",
    "brvbar;": "\u00A6",
    "brvbar": "\u00A6",
    "bull;": "\u2022",
    "cap;": "\u2229",
    "ccedil;": "\u00E7",
    "ccedil": "\u00E7",
    "cedil;": "\u00B8",
    "cedil": "\u00B8",
    "cent;": "\u00A2",
    "cent": "\u00A2",
    "chi;": "\u03C7",
    "circ;": "\u02C6",
    "clubs;": "\u2663",
    "cong;": "\u2245",
    "copy;": "\u00A9",
    "copy": "\u00A9",
    "crarr;": "\u21B5",
    "cup;": "\u222A",
    "curren;": "\u00A4",
    "curren": "\u00A4",
    "dArr;": "\u21D3",
    "dagger;": "\u2020",
    "darr;": "\u2193",
    "deg;": "\u00B0",
    "deg": "\u00B0",
    "delta;": "\u03B4",
    "diams;": "\u2666",
    "divide;": "\u00F7",
    "divide": "\u00F7",
    "eacute;": "\u00E9",
    "eacute": "\u00E9",
    "ecirc;": "\u00EA",
    "ecirc": "\u00EA",
    "egrave;": "\u00E8",
    "egrave": "\u00E8",
    "empty;": "\u2205",
    "emsp;": "\u2003",
    "ensp;": "\u2002",
    "epsilon;": "\u03B5",
    "equiv;": "\u2261",
    "eta;": "\u03B7",
    "eth;": "\u00F0",
    "eth": "\u00F0",
    "euml;": "\u00EB",
    "euml": "\u00EB",
    "euro;": "\u20AC",
    "exist;": "\u2203",
    "fnof;": "\u0192",
    "forall;": "\u2200",
    "frac12;": "\u00BD",
    "frac12": "\u00BD",
    "frac14;": "\u00BC",
    "frac14": "\u00BC",
    "frac34;": "\u00BE",
    "frac34": "\u00BE",
    "frasl;": "\u2044",
    "gamma;": "\u03B3",
    "ge;": "\u2265",
    "gt;": "\u003E",
    "gt": "\u003E",
    "hArr;": "\u21D4",
    "harr;": "\u2194",
    "hearts;": "\u2665",
    "hellip;": "\u2026",
    "iacute;": "\u00ED",
    "iacute": "\u00ED",
    "icirc;": "\u00EE",
    "icirc": "\u00EE",
    "iexcl;": "\u00A1",
    "iexcl": "\u00A1",
    "igrave;": "\u00EC",
    "igrave": "\u00EC",
    "image;": "\u2111",
    "infin;": "\u221E",
    "int;": "\u222B",
    "iota;": "\u03B9",
    "iquest;": "\u00BF",
    "iquest": "\u00BF",
    "isin;": "\u2208",
    "iuml;": "\u00EF",
    "iuml": "\u00EF",
    "kappa;": "\u03BA",
    "lArr;": "\u21D0",
    "lambda;": "\u03BB",
    "lang;": "\u27E8",
    "laquo;": "\u00AB",
    "laquo": "\u00AB",
    "larr;": "\u2190",
    "lceil;": "\u2308",
    "ldquo;": "\u201C",
    "le;": "\u2264",
    "lfloor;": "\u230A",
    "lowast;": "\u2217",
    "loz;": "\u25CA",
    "lrm;": "\u200E",
    "lsaquo;": "\u2039",
    "lsquo;": "\u2018",
    "lt;": "\u003C",
    "lt": "\u003C",
    "macr;": "\u00AF",
    "macr": "\u00AF",
    "mdash;": "\u2014",
    "micro;": "\u00B5",
    "micro": "\u00B5",
    "middot;": "\u00B7",
    "middot": "\u00B7",
    "minus;": "\u2212",
    "mu;": "\u03BC",
    "nabla;": "\u2207",
    "nbsp;": "\u00A0",
    "nbsp": "\u00A0",
    "ndash;": "\u2013",
    "ne;": "\u2260",
    "ni;": "\u220B",
    "not;": "\u00AC",
    "not": "\u00AC",
    "notin;": "\u2209",
    "nsub;": "\u2284",
    "ntilde;": "\u00F1",
    "ntilde": "\u00F1",
    "nu;": "\u03BD",
    "oacute;": "\u00F3",
    "oacute": "\u00F3",
    "ocirc;": "\u00F4",
    "ocirc": "\u00F4",
    "oelig;": "\u0153",
    "ograve;": "\u00F2",
    "ograve": "\u00F2",
    "oline;": "\u203E",
    "omega;": "\u03C9",
    "omicron;": "\u03BF",
    "oplus;": "\u2295",
    "or;": "\u2228",
    "ordf;": "\u00AA",
    "ordf": "\u00AA",
    "ordm;": "\u00BA",
    "ordm": "\u00BA",
    "oslash;": "\u00F8",
    "oslash": "\u00F8",
    "otilde;": "\u00F5",
    "otilde": "\u00F5",
    "otimes;": "\u2297",
    "ouml;": "\u00F6",
    "ouml": "\u00F6",
    "para;": "\u00B6",
    "para": "\u00B6",
    "part;": "\u2202",
    "permil;": "\u2030",
    "perp;": "\u22A5",
    "phi;": "\u03C6",
    "pi;": "\u03C0",
    "piv;": "\u03D6",
    "plusmn;": "\u00B1",
    "plusmn": "\u00B1",
    "pound;": "\u00A3",
    "pound": "\u00A3",
    "prime;": "\u2032",
    "prod;": "\u220F",
    "prop;": "\u221D",
    "psi;": "\u03C8",
    "quot;": "\u0022",
    "quot": "\u0022",
    "rArr;": "\u21D2",
    "radic;": "\u221A",
    "rang;": "\u27E9",
    "raquo;": "\u00BB",
    "raquo": "\u00BB",
    "rarr;": "\u2192",
    "rceil;": "\u2309",
    "rdquo;": "\u201D",
    "real;": "\u211C",
    "reg;": "\u00AE",
    "reg": "\u00AE",
    "rfloor;": "\u230B",
    "rho;": "\u03C1",
    "rlm;": "\u200F",
    "rsaquo;": "\u203A",
    "rsquo;": "\u2019",
    "sbquo;": "\u201A",
    "scaron;": "\u0161",
    "sdot;": "\u22C5",
    "sect;": "\u00A7",
    "sect": "\u00A7",
    "shy;": "\u00AD",
    "shy": "\u00AD",
    "sigma;": "\u03C3",
    "sigmaf;": "\u03C2",
    "sim;": "\u223C",
    "spades;": "\u2660",
    "sub;": "\u2282",
    "sube;": "\u2286",
    "sum;": "\u2211",
    "sup1;": "\u00B9",
    "sup1": "\u00B9",
    "sup2;": "\u00B2",
    "sup2": "\u00B2",
    "sup3;": "\u00B3",
    "sup3": "\u00B3",
    "sup;": "\u2283",
    "supe;": "\u2287",
    "szlig;": "\u00DF",
    "szlig": "\u00DF",
    "tau;": "\u03C4",
    "there4;": "\u2234",
    "theta;": "\u03B8",
    "thetasym;": "\u03D1",
    "thinsp;": "\u2009",
    "thorn;": "\u00FE",
    "thorn": "\u00FE",
    "tilde;": "\u02DC",
    "times;": "\u00D7",
    "times": "\u00D7",
    "trade;": "\u2122",
    "uArr;": "\u21D1",
    "uacute;": "\u00FA",
    "uacute": "\u00FA",
    "uarr;": "\u2191",
    "ucirc;": "\u00FB",
    "ucirc": "\u00FB",
    "ugrave;": "\u00F9",
    "ugrave": "\u00F9",
    "uml;": "\u00A8",
    "uml": "\u00A8",
    "upsih;": "\u03D2",
    "upsilon;": "\u03C5",
    "uuml;": "\u00FC",
    "uuml": "\u00FC",
    "weierp;": "\u2118",
    "xi;": "\u03BE",
    "yacute;": "\u00FD",
    "yacute": "\u00FD",
    "yen;": "\u00A5",
    "yen": "\u00A5",
    "yuml;": "\u00FF",
    "yuml": "\u00FF",
    "zeta;": "\u03B6",
    "zwj;": "\u200D",
    "zwnj;": "\u200C"
}

encodings = {
    '437': 'cp437',
    '850': 'cp850',
    '852': 'cp852',
    '855': 'cp855',
    '857': 'cp857',
    '860': 'cp860',
    '861': 'cp861',
    '862': 'cp862',
    '863': 'cp863',
    '865': 'cp865',
    '866': 'cp866',
    '869': 'cp869',
    'ansix341968': 'ascii',
    'ansix341986': 'ascii',
    'arabic': 'iso8859-6',
    'ascii': 'ascii',
    'asmo708': 'iso8859-6',
    'big5': 'big5',
    'big5hkscs': 'big5hkscs',
    'chinese': 'gbk',
    'cp037': 'cp037',
    'cp1026': 'cp1026',
    'cp154': 'ptcp154',
    'cp367': 'ascii',
    'cp424': 'cp424',
    'cp437': 'cp437',
    'cp500': 'cp500',
    'cp775': 'cp775',
    'cp819': 'windows-1252',
    'cp850': 'cp850',
    'cp852': 'cp852',
    'cp855': 'cp855',
    'cp857': 'cp857',
    'cp860': 'cp860',
    'cp861': 'cp861',
    'cp862': 'cp862',
    'cp863': 'cp863',
    'cp864': 'cp864',
    'cp865': 'cp865',
    'cp866': 'cp866',
    'cp869': 'cp869',
    'cp936': 'gbk',
    'cpgr': 'cp869',
    'cpis': 'cp861',
    'csascii': 'ascii',
    'csbig5': 'big5',
    'cseuckr': 'windows-949',
    'cseucpkdfmtjapanese': 'euc_jp',
    'csgb2312': 'gbk',
    'cshproman8': 'hp-roman8',
    'csibm037': 'cp037',
    'csibm1026': 'cp1026',
    'csibm424': 'cp424',
    'csibm500': 'cp500',
    'csibm855': 'cp855',
    'csibm857': 'cp857',
    'csibm860': 'cp860',
    'csibm861': 'cp861',
    'csibm863': 'cp863',
    'csibm864': 'cp864',
    'csibm865': 'cp865',
    'csibm866': 'cp866',
    'csibm869': 'cp869',
    'csiso2022jp': 'iso2022_jp',
    'csiso2022jp2': 'iso2022_jp_2',
    'csiso2022kr': 'iso2022_kr',
    'csiso58gb231280': 'gbk',
    'csisolatin1': 'windows-1252',
    'csisolatin2': 'iso8859-2',
    'csisolatin3': 'iso8859-3',
    'csisolatin4': 'iso8859-4',
    'csisolatin5': 'windows-1254',
    'csisolatin6': 'iso8859-10',
    'csisolatinarabic': 'iso8859-6',
    'csisolatincyrillic': 'iso8859-5',
    'csisolatingreek': 'iso8859-7',
    'csisolatinhebrew': 'iso8859-8',
    'cskoi8r': 'koi8-r',
    'csksc56011987': 'windows-949',
    'cspc775baltic': 'cp775',
    'cspc850multilingual': 'cp850',
    'cspc862latinhebrew': 'cp862',
    'cspc8codepage437': 'cp437',
    'cspcp852': 'cp852',
    'csptcp154': 'ptcp154',
    'csshiftjis': 'shift_jis',
    'csunicode11utf7': 'utf-7',
    'cyrillic': 'iso8859-5',
    'cyrillicasian': 'ptcp154',
    'ebcdiccpbe': 'cp500',
    'ebcdiccpca': 'cp037',
    'ebcdiccpch': 'cp500',
    'ebcdiccphe': 'cp424',
    'ebcdiccpnl': 'cp037',
    'ebcdiccpus': 'cp037',
    'ebcdiccpwt': 'cp037',
    'ecma114': 'iso8859-6',
    'ecma118': 'iso8859-7',
    'elot928': 'iso8859-7',
    'eucjp': 'euc_jp',
    'euckr': 'windows-949',
    'extendedunixcodepackedformatforjapanese': 'euc_jp',
    'gb18030': 'gb18030',
    'gb2312': 'gbk',
    'gb231280': 'gbk',
    'gbk': 'gbk',
    'greek': 'iso8859-7',
    'greek8': 'iso8859-7',
    'hebrew': 'iso8859-8',
    'hproman8': 'hp-roman8',
    'hzgb2312': 'hz',
    'ibm037': 'cp037',
    'ibm1026': 'cp1026',
    'ibm367': 'ascii',
    'ibm424': 'cp424',
    'ibm437': 'cp437',
    'ibm500': 'cp500',
    'ibm775': 'cp775',
    'ibm819': 'windows-1252',
    'ibm850': 'cp850',
    'ibm852': 'cp852',
    'ibm855': 'cp855',
    'ibm857': 'cp857',
    'ibm860': 'cp860',
    'ibm861': 'cp861',
    'ibm862': 'cp862',
    'ibm863': 'cp863',
    'ibm864': 'cp864',
    'ibm865': 'cp865',
    'ibm866': 'cp866',
    'ibm869': 'cp869',
    'iso2022jp': 'iso2022_jp',
    'iso2022jp2': 'iso2022_jp_2',
    'iso2022kr': 'iso2022_kr',
    'iso646irv1991': 'ascii',
    'iso646us': 'ascii',
    'iso88591': 'windows-1252',
    'iso885910': 'iso8859-10',
    'iso8859101992': 'iso8859-10',
    'iso885911987': 'windows-1252',
    'iso885913': 'iso8859-13',
    'iso885914': 'iso8859-14',
    'iso8859141998': 'iso8859-14',
    'iso885915': 'iso8859-15',
    'iso885916': 'iso8859-16',
    'iso8859162001': 'iso8859-16',
    'iso88592': 'iso8859-2',
    'iso885921987': 'iso8859-2',
    'iso88593': 'iso8859-3',
    'iso885931988': 'iso8859-3',
    'iso88594': 'iso8859-4',
    'iso885941988': 'iso8859-4',
    'iso88595': 'iso8859-5',
    'iso885951988': 'iso8859-5',
    'iso88596': 'iso8859-6',
    'iso885961987': 'iso8859-6',
    'iso88597': 'iso8859-7',
    'iso885971987': 'iso8859-7',
    'iso88598': 'iso8859-8',
    'iso885981988': 'iso8859-8',
    'iso88599': 'windows-1254',
    'iso885991989': 'windows-1254',
    'isoceltic': 'iso8859-14',
    'isoir100': 'windows-1252',
    'isoir101': 'iso8859-2',
    'isoir109': 'iso8859-3',
    'isoir110': 'iso8859-4',
    'isoir126': 'iso8859-7',
    'isoir127': 'iso8859-6',
    'isoir138': 'iso8859-8',
    'isoir144': 'iso8859-5',
    'isoir148': 'windows-1254',
    'isoir149': 'windows-949',
    'isoir157': 'iso8859-10',
    'isoir199': 'iso8859-14',
    'isoir226': 'iso8859-16',
    'isoir58': 'gbk',
    'isoir6': 'ascii',
    'koi8r': 'koi8-r',
    'koi8u': 'koi8-u',
    'korean': 'windows-949',
    'ksc5601': 'windows-949',
    'ksc56011987': 'windows-949',
    'ksc56011989': 'windows-949',
    'l1': 'windows-1252',
    'l10': 'iso8859-16',
    'l2': 'iso8859-2',
    'l3': 'iso8859-3',
    'l4': 'iso8859-4',
    'l5': 'windows-1254',
    'l6': 'iso8859-10',
    'l8': 'iso8859-14',
    'latin1': 'windows-1252',
    'latin10': 'iso8859-16',
    'latin2': 'iso8859-2',
    'latin3': 'iso8859-3',
    'latin4': 'iso8859-4',
    'latin5': 'windows-1254',
    'latin6': 'iso8859-10',
    'latin8': 'iso8859-14',
    'latin9': 'iso8859-15',
    'ms936': 'gbk',
    'mskanji': 'shift_jis',
    'pt154': 'ptcp154',
    'ptcp154': 'ptcp154',
    'r8': 'hp-roman8',
    'roman8': 'hp-roman8',
    'shiftjis': 'shift_jis',
    'tis620': 'windows-874',
    'unicode11utf7': 'utf-7',
    'us': 'ascii',
    'usascii': 'ascii',
    'utf16': 'utf-16',
    'utf16be': 'utf-16-be',
    'utf16le': 'utf-16-le',
    'utf7': 'utf-7',
    'utf8': 'utf-8',
    'windows1250': 'cp1250',
    'windows1251': 'cp1251',
    'windows1252': 'cp1252',
    'windows1253': 'cp1253',
    'windows1254': 'cp1254',
    'windows1255': 'cp1255',
    'windows1256': 'cp1256',
    'windows1257': 'cp1257',
    'windows1258': 'cp1258',
    'windows936': 'gbk',
    'x-x-big5': 'big5'}

tokenTypes = {
    "Doctype":0,
    "Characters":1,
    "SpaceCharacters":2,
    "StartTag":3,
    "EndTag":4,
    "EmptyTag":5,
    "Comment":6,
    "ParseError":7
}

namespaces = {
    "html":"http://www.w3.org/1999/xhtml",
    "mathml":"http://www.w3.org/1998/Math/MathML",
    "svg":"http://www.w3.org/2000/svg",
    "xlink":"http://www.w3.org/1999/xlink",
    "xml":"http://www.w3.org/XML/1998/namespace",
    "xmlns":"http://www.w3.org/2000/xmlns/"
}


class DataLossWarning(UserWarning):
    pass

class ReparseException(Exception):
    pass
