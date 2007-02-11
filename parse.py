#!/usr/bin/env python
"""usage: %prog [options] filename

Parse a document to a simpletree tree, with optional profiling
"""

import sys
import os
from optparse import OptionParser

from src import html5parser, liberalxmlparser

def convertTreeDump(treedump):
    """convert the output of str(document) to something more readable
    """
    treedump = treedump.split("\n")[1:]
    rv = []
    for line in treedump:
        if line.startswith("|"):
            rv.append(line[3:])
        else:
            rv.append(line)
    return "\n".join(rv)

def parse():
    optParser = getOptParser()
    opts,args = optParser.parse_args()

    try:
        f = args[-1]
        # Try opening from the internet
        if f.startswith('http://'):
            try:
                import urllib
                f = urllib.urlopen(f).read()
            except: pass
        else:
            try:
                # Try opening from file system
                f = open(f)
            except IOError: pass
    except IndexError:
        sys.stderr.write("No filename provided. Use -h for help")
        sys.exit(1)

    if opts.treebuilder is not None:
        try:
            treebuilder = __import__("src.treebuilders." + opts.treebuilder,
                None,None,"src").TreeBuilder
        except ImportError, name:
            sys.stderr.write("Treebuilder %s not found"%name)
            raise
        except Exception, foo:
            import src.treebuilders.simpletree
            treebuilder = src.treebuilders.simpletree.TreeBuilder
    else:
        import src.treebuilders.simpletree
        treebuilder = src.treebuilders.simpletree.TreeBuilder

    if opts.xml:
        p = liberalxmlparser.XHTMLParser(tree=treebuilder)
    else:
        p = html5parser.HTMLParser(tree=treebuilder)

    if opts.profile:
        import hotshot
        import hotshot.stats
        prof = hotshot.Profile('stats.prof')
        prof.runcall(p.parse, f, False)
        prof.close()
        # XXX - We should use a temp file here
        stats = hotshot.stats.load('stats.prof')
        stats.strip_dirs()
        stats.sort_stats('time')
        stats.print_stats()
    elif opts.time:
        import time
        t0 = time.time()
        document = p.parse(f)
        t1 = time.time()
        printOutput(p, document, opts)
        t2 = time.time()
        sys.stdout.write("\n\nRun took: %fs (plus %fs to print the output)"%(t1-t0, t2-t1))
    else:
        document = p.parse(f)
        printOutput(p, document, opts)

def printOutput(parser, document, opts):
    if opts.xml:
        sys.stdout.write(document.toxml("utf-8"))
    elif opts.hilite:
        sys.stdout.write(document.hilite("utf-8"))
    else:
        sys.stdout.write(parser.tree.testSerializer(document).encode("utf-8"))
    if opts.error:
        errList=[]
        for pos, message in parser.errors:
            errList.append("Line %i Col %i"%pos + " " + message)
        sys.stderr.write("\nParse errors:\n" + "\n".join(errList))

def getOptParser():
    parser = OptionParser(usage=__doc__)

    parser.add_option("-p", "--profile", action="store_true", default=False,
                      dest="profile", help="Use the hotshot profiler to "
                      "produce a detailed log of the run")

    parser.add_option("-t", "--time",
                      action="store_true", default=False, dest="time",
                      help="Time the run using time.time (may not be accurate on all platforms, especially for short runs)")

    parser.add_option("-b", "--treebuilder", action="store", type="string",
                      dest="treebuilder")

    parser.add_option("-e", "--error", action="store_true", default=False,
                      dest="error", help="Print a list of parse errors")

    parser.add_option("-x", "--xml", action="store_true", default=False,
                      dest="xml", help="Output as xml")
    
    parser.add_option("", "--hilite", action="store_true", default=False,
                      dest="hilite", help="Output as formatted highlighted code.")

    return parser

if __name__ == "__main__":
    parse()
