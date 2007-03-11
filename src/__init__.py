""" 
HTML parsing library based on the WHATWG "HTML5"
specification. The parser is designed to be compatible with existing
HTML found in the wild and implements well-defined error recovery that
is largely compatible with modern desktop web browsers.

Example usage:

import html5lib
f = open("my_document.html")
p = html5lib.HTMLParser()
tree = p.parse(f) 
"""
from html5parser import HTMLParser
from liberalxmlparser import XMLParser, XHTMLParser
