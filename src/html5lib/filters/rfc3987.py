# adapted from feedvalidator, original copyright license is
#
# Copyright (c) 2002-2006, Sam Ruby, Mark Pilgrim, Joseph Walton, and Phil Ringnalda
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

iana_schemes = [ # http://www.iana.org/assignments/uri-schemes.html
  "ftp", "http", "gopher", "mailto", "news", "nntp", "telnet", "wais",
  "file", "prospero", "z39.50s", "z39.50r", "cid", "mid", "vemmi",
  "service", "imap", "nfs", "acap", "rtsp", "tip", "pop", "data", "dav",
  "opaquelocktoken", "sip", "sips", "tel", "fax", "modem", "ldap",
  "https", "soap.beep", "soap.beeps", "xmlrpc.beep", "xmlrpc.beeps",
  "urn", "go", "h323", "ipp", "tftp", "mupdate", "pres", "im", "mtqp",
  "iris.beep", "dict", "snmp", "crid", "tag", "dns", "info"
]
allowed_schemes = iana_schemes + ['javascript']

rfc2396_re = re.compile("([a-zA-Z][0-9a-zA-Z+\\-\\.]*:)?/{0,2}" +
                        "[0-9a-zA-Z;/?:@&=+$\\.\\-_!~*'()%,#]*$")
rfc2396_full_re = re.compile("[a-zA-Z][0-9a-zA-Z+\\-\\.]*:(//)?" +
                             "[0-9a-zA-Z;/?:@&=+$\\.\\-_!~*'()%,#]+$")
urn_re = re.compile(r"^[Uu][Rr][Nn]:[a-zA-Z0-9][a-zA-Z0-9-]{1,31}:([a-zA-Z0-9()+,\.:=@;$_!*'\-]|%[0-9A-Fa-f]{2})+$")
tag_re = re.compile(r"^tag:([a-z0-9\-\._]+?@)?[a-z0-9\.\-]+?,\d{4}(-\d{2}(-\d{2})?)?:[0-9a-zA-Z;/\?:@&=+$\.\-_!~*'\(\)%,]*(#[0-9a-zA-Z;/\?:@&=+$\.\-_!~*'\(\)%,]*)?$")

def isValidURI(value, uriPattern=rfc2396_re):
    scheme=value.split(':')[0].lower()
    if scheme == 'tag':
        if not tag_re.match(value):
            return False, "invalid-tag-uri"
    elif scheme == "urn":
        if not urn_re.match(value):
            return False, "invalid-urn"
    elif not uriPattern.match(value):
        urichars_re=re.compile("[0-9a-zA-Z;/?:@&=+$\\.\\-_!~*'()%,#]")
        for c in value:
            if ord(c)<128 and not urichars_re.match(c):
                return False, "invalid-uri-char"
        else:
            try:
                if uriPattern.match(value.encode('idna')):
                    return False, "uri-not-iri"
            except:
                pass
            return False, "invalid-uri"
    elif scheme in ['http','ftp']:
        if not re.match('^\w+://[^/].*',value):
            return False, "invalid-http-or-ftp-uri"
    elif value.find(':')>=0 and scheme.isalpha() and scheme not in allowed_schemes:
        return False, "invalid-scheme"
    return True, ""

def isValidIRI(value):
    try:
        if value: value = value.encode('idna')
    except:
        pass
    return isValidURI(value)

def isValidFullyQualifiedURI(value):
    return isValidURI(value, rfc2396_full_re)

