#!/usr/bin/env python

import sys
import urllib2
import cgi

import html5lib

htmlTemplate = u"""<html>
<head>
<title>%(title)s</title>
</head>
<body>
<h1>%(title)s</h1>
%(body)s
</body>
</html>"""

def parseDocument(document):
    """Parse the document and return a list of errors and a parse tree"""
    p = html5lib.HTMLParser()
    tree = p.parse(document)
    return p.errors, cgi.escape(tree.printTree(), True)

def getDocument(uri):
    if uri.startswith("http://") or uri.startswith("https://"):
        #Why is string conversion necessary here?
        document = "".join(urllib2.urlopen(uri).readlines())[:-1]
        #print "<--!%s-->"%(document,)
    else:
        raise ValueError, "Unrecognised URI type"
    return document

def writeValid(uri, treeStr):
    bodyText = """<p><strong>%s is valid HTML5!</strong></p>
<h2>Parse Tree:</h2>
<pre>
%s
</pre>"""%(uri, treeStr)
    writeOutput(htmlTemplate%{"title":"Validation Results", "body":bodyText})

def writeInvalid(uri, treeStr, errors):
    errList=[]
    for pos, message in errors:
        errList.append("Line %i Col %i"%pos + " " + message)
    errStr = "<br>\n".join(errList)
    bodyText = """<p><strong>%s is not valid HTML5</strong></p>
<h2>Errors:</h2>
%s
<h2>Parse Tree:</h2>
<pre>
%s
</pre>"""%(uri, errStr, treeStr)
    writeOutput(htmlTemplate%{"title":"Validation Results", "body":bodyText})

def writeErr(uri):
    bodyText = "<p>Failed to load URI %s</p>"%(uri,)
    writeOutput(htmlTemplate%{"title":"Error", "body":bodyText})

def writeOutput(s):
    print s.encode('utf-8')

print "Content-type: text/html"
print ""

try:
    form = cgi.FieldStorage()
    uri = form.getvalue("uri")
    document = getDocument(uri)
except:
    writeErr(uri)
    sys.exit(1)

errors, tree = parseDocument(document)
if errors:
    writeInvalid(uri, tree, errors)
else:
    writeValid(uri, tree)
