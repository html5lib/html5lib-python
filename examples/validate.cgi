#!/usr/bin/env python

"""This is a toy example not a serious conformance checker. In
particular, it only reports parse errors when reading the document; it
does not report any of the other (many) possible types of conformance
errors that may exist in a HTML5 document"""

import sys
import cgi
import copy

import httplib2
import lxml
from genshi.template import MarkupTemplate

import html5lib
from html5lib import treebuilders

class Resource(object):
    http = httplib2.Http()
    def __init__(self, uri):
        self.uri = uri
        self.content = None
    
    def load(self):
        self.response, self.content = self.http.request(self.uri)

    def parse(self):
        raise NotImplementedError

class Schema(Resource):
    def load(self):
        #This will just be a network operation eventually
        self.content = open(self.uri).read()
    
    def parse(self):
        self.tree = lxml.etree.parse(self.content)
        self.relaxng = lxml.etree.RelaxNG(self.tree)

class Document(Resource):
    
    def parse(self):
        parser = html5lib.HTMLParser(
            tree=treebuilders.getTreeBuilder("etree", lxml.etree))
        self.tree = parser.parse(self.content)
        self.parseErrors = parser.parseErrors
        self.hasSyntaxErrors = not(self.parseErrors)
    
    def check(self, schema):
        self.hasConformaceErrors = schema.relaxng.validate(self.tree)
        self.relaxErrors = schema.relaxng.error_log

class Response(object):
    templateFilename = "response.html"
    def __init__(self):
        self.template = MarkupTemplate(open(self.templateFilename).read())
    
    def render(self, document):
        stream = self.template.generate(doc = document)
        return stream.render(doctype=("html","",""))