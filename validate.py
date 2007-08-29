#!/usr/bin/env python
"""usage: %prog [options] url-or-filename

Validate an HTML5 document using a non-schema-based conformance checker"""
#RELEASE move ./examples/

import sys
import os
from optparse import OptionParser

#RELEASE remove
sys.path.insert(0,os.path.abspath(os.path.join(__file__,'../src')))
#END RELEASE
from html5lib import html5parser#, liberalxmlparser
from html5lib import treebuilders
from html5lib import constants
from html5lib.filters import validator

def parse():
    optParser = getOptParser()
    opts,args = optParser.parse_args()
    encoding = None

    try:
        f = args[-1]
        # Try opening from the internet
        if f.startswith('http://'):
            try:
                import urllib, cgi
                f = urllib.urlopen(f)
                contentType = f.headers.get('content-type')
                if contentType:
                    (mediaType, params) = cgi.parse_header(contentType)
                    encoding = params.get('charset')
            except: pass
        elif f == '-':
            f = sys.stdin
        else:
            try:
                # Try opening from file system
                f = open(f)
            except IOError: pass
    except IndexError:
        sys.stderr.write("No filename provided. Use -h for help\n")
        sys.exit(1)

    treebuilder = treebuilders.getTreeBuilder("simpleTree")

#    if opts.xml:
#        p = liberalxmlparser.XHTMLParser(tree=treebuilder)
#    else:
    if 1:
        p = html5parser.HTMLParser(tree=treebuilder, tokenizer=validator.HTMLConformanceChecker)

    document = p.parse(f, encoding=encoding)
    printOutput(p, document, opts)

def printOutput(parser, document, opts):
    errList=[]
    for pos, errorcode, datavars in parser.errors:
        errList.append("Line %i Col %i"%pos + " " + constants.E.get(errorcode, 'Unknown error "%s"' % errorcode) % datavars)
    sys.stdout.write("\nValidation errors:\n" + "\n".join(errList)+"\n")

def getOptParser():
    parser = OptionParser(usage=__doc__)
    return parser

if __name__ == "__main__":
    parse()
