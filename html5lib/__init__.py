# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
HTML parsing library based on the WHATWG "HTML5"
specification. The parser is designed to be compatible with existing
HTML found in the wild and implements well-defined error recovery that
is largely compatible with modern desktop web browsers.

Example usage:

import html5lib
f = open("my_document.html")
tree = html5lib.parse(f)
"""

from __future__ import absolute_import, division, unicode_literals

from .html5parser import HTMLParser, parse, parseFragment
from .treebuilders import getTreeBuilder
from .treewalkers import getTreeWalker
from .serializer import serialize

__all__ = ["HTMLParser", "parse", "parseFragment", "getTreeBuilder",
           "getTreeWalker", "serialize"]

# this has to be at the top level, see how setup.py parses this
__version__ = "0.9999999999-dev"
