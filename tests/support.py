import os
import sys
import glob

#Allow us to import the parent module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

#RELEASE remove
import html5parser
#Run tests over all treebuilders
#XXX - it would be nice to automate finding all treebuilders or to allow running just one

import treebuilders
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser
#from html5lib.treebuilders import simpletree, etreefull, dom
#END RELEASE

try:
    import simplejson
except:
    import re
    class simplejson:
        def load(f):
            true, false, null = True, False, None
            input = re.sub(r'(".*?(?<!\\)")',r'u\1',f.read().decode('utf-8'))
            return eval(input.replace('\r',''))
        load = staticmethod(load)

#Build a dict of avaliable trees
treeTypes = {"simpletree":treebuilders.getTreeBuilder("simpletree"),
             "DOM":treebuilders.getTreeBuilder("dom")}

#Try whatever etree implementations are avaliable from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes['lxml'] = treebuilders.getTreeBuilder("etree", lxml, fullTree=True)
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treebuilders.getTreeBuilder("beautifulsoup", fullTree=True)
except ImportError:
    pass

def html5lib_test_files(subdirectory, files='*.dat'):
    return glob.glob(os.path.join(os.path.pardir,os.path.pardir,'testdata',subdirectory,files))

class TestData(object):
    def __init__(self, filename, sections):
        self.f = open(filename)
        self.sections = sections
    
    def __iter__(self):
        data = {}
        key=None
        for line in self.f:
            heading = self.isSectionHeading(line)
            if heading:
                if data and heading == self.sections[0]:
                    #Remove trailing newline
                    data[key] = data[key][:-1]
                    yield self.normaliseOutput(data)
                    data = {}
                key = heading
                data[key]=""
            elif key is not None:
                data[key] += line
        if data:
            yield self.normaliseOutput(data)
        
    def isSectionHeading(self, line):
        """If the current heading is a test section heading return the heading,
        otherwise return False"""
        line=line.strip()
        if line.startswith("#") and line[1:] in self.sections:
            return line[1:]
        else:
            return False
    
    def normaliseOutput(self, data):
        #Remove trailing newlines
        for key,value in data.iteritems():
            if value.endswith("\n"):
                data[key] = value[:-1]
        for heading in self.sections:
            if heading not in data:
                data[heading] = None
        return data