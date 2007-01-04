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

By default the returned treeformat is a custom "simpletree", similar
to a DOM tree; each element has attributes childNodes and parent
holding the parents and children respectively, a name attribute
holding the Element name, a data attribute holding the element data
(for text and comment nodes) and an attributes dictionary holding the
element's attributes (for Element nodes).

To get output in ElementTree format:

import html5lib
from html5lib.treebuilders import etree
p = html5lib.HTMLParser(tree=etree.TreeBuilder)
elementtree = p.parse(f)

Note: Because HTML documents support various features not in the
default ElementTree (e.g. doctypes), we suppy our own simple
serializer; html5lib.treebuilders.etree.write At present this does not
have the encoding support offered by the elementtree serializer.

"""
from parser import HTMLParser
