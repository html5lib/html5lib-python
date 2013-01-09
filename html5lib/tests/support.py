from __future__ import absolute_import
import os
import sys
import codecs
import glob
from io import open

base_path = os.path.split(__file__)[0]

if os.path.exists(os.path.join(base_path, u'testdata')):
    #release
    test_dir = os.path.join(base_path, u'testdata')
else:
    #development
    test_dir = os.path.abspath(
        os.path.join(base_path,
                     os.path.pardir, os.path.pardir,
                     os.path.pardir, u'testdata'))
    assert os.path.exists(test_dir), u"Test data not found"
    #import the development html5lib
    sys.path.insert(0, os.path.abspath(os.path.join(base_path, 
                                                    os.path.pardir,
                                                    os.path.pardir)))

import html5lib
from html5lib import html5parser, treebuilders
del base_path

#Build a dict of avaliable trees
treeTypes = {u"simpletree":treebuilders.getTreeBuilder(u"simpletree"),
             u"DOM":treebuilders.getTreeBuilder(u"dom")}

#Try whatever etree implementations are avaliable from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes[u'ElementTree'] = treebuilders.getTreeBuilder(u"etree", ElementTree, fullTree=True)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes[u'ElementTree'] = treebuilders.getTreeBuilder(u"etree", ElementTree, fullTree=True)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes[u'cElementTree'] = treebuilders.getTreeBuilder(u"etree", cElementTree, fullTree=True)
except ImportError:
    try:
        import cElementTree
        treeTypes[u'cElementTree'] = treebuilders.getTreeBuilder(u"etree", cElementTree, fullTree=True)
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes[u'lxml'] = treebuilders.getTreeBuilder(u"lxml")
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes[u"beautifulsoup"] = treebuilders.getTreeBuilder(u"beautifulsoup", fullTree=True)
except ImportError:
    pass

def get_data_files(subdirectory, files=u'*.dat'):
    return glob.glob(os.path.join(test_dir,subdirectory,files))
get_data_files.func_annotations = {}

class DefaultDict(dict):
    def __init__(self, default, *args, **kwargs):
        self.default = default
        dict.__init__(self, *args, **kwargs)
    __init__.func_annotations = {}
    
    def __getitem__(self, key):
        return dict.get(self, key, self.default)
    __getitem__.func_annotations = {}

class TestData(object):
    def __init__(self, filename, newTestHeading=u"data", encoding=u"utf8"):
        if encoding == None:
            self.f = open(filename, mode=u"rb")
        else:
            self.f = codecs.open(filename, encoding=encoding)
        self.encoding = encoding
        self.newTestHeading = newTestHeading
    __init__.func_annotations = {}

    def __del__(self):
        self.f.close()
    __del__.func_annotations = {}
    
    def __iter__(self):
        data = DefaultDict(None)
        key=None
        for line in self.f:
            heading = self.isSectionHeading(line)
            if heading:
                if data and heading == self.newTestHeading:
                    #Remove trailing newline
                    data[key] = data[key][:-1]
                    yield self.normaliseOutput(data)
                    data = DefaultDict(None)
                key = heading
                data[key]=u"" if self.encoding else ""
            elif key is not None:
                data[key] += line
        if data:
            yield self.normaliseOutput(data)
    __iter__.func_annotations = {}
        
    def isSectionHeading(self, line):
        u"""If the current heading is a test section heading return the heading,
        otherwise return False"""
        #print(line)
        if line.startswith(u"#" if self.encoding else "#"):
            return line[1:].strip()
        else:
            return False
    isSectionHeading.func_annotations = {}
    
    def normaliseOutput(self, data):
        #Remove trailing newlines
        for key,value in data.items():
            if value.endswith(u"\n" if self.encoding else "\n"):
                data[key] = value[:-1]
        return data
    normaliseOutput.func_annotations = {}

def convert(stripChars):
    def convertData(data):
        u"""convert the output of str(document) to the format used in the testcases"""
        data = data.split(u"\n")
        rv = []
        for line in data:
            if line.startswith(u"|"):
                rv.append(line[stripChars:])
            else:
                rv.append(line)
        return u"\n".join(rv)
    convertData.func_annotations = {}
    return convertData
convert.func_annotations = {}

convertExpected = convert(2)

def errorMessage(input, expected, actual):
    msg = (u"Input:\n%s\nExpected:\n%s\nRecieved\n%s\n" %
           (repr(input), repr(expected), repr(actual)))
    if sys.version_info.major == 2:
        msg = msg.encode(u"ascii", u"backslashreplace")
    return msg
errorMessage.func_annotations = {}
