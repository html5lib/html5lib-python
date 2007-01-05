#!/usr/bin/env python
"""usage: %prog [options] filename

Parse a document to a simpletree tree, with optional profiling
"""

import sys
import os
from optparse import OptionParser

from src import parser, treebuilders

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
    except IndexError:
        print "No filename provided. Use -h for help"
        sys.exit(1)
    if opts.treebuilder is not None:
        try:
            #This isn't a great way to do this
            exec("import treebuilders.%s")%opts.treebuilder.split(".")[0]
            treebuilder = eval("treebuilders.%s"%opts.treebuilder)
        except NameError:
            print "Treebuilder %s not found"%opts.treebuilder 
            raise
        except:
            treebuilder = treebuilders.simpletree.TreeBuilder
    else:
        import treebuilders.simpletree
        treebuilder = treebuilders.simpletree.TreeBuilder

    p = parser.HTMLParser(tree=treebuilder)

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
        print p.tree.testSerializer(document)
        if opts.error:
            print "\nParse errors:\n" + "\n".join(p.errors)
        t2 = time.time()
        print "\n\nRun took: %fs (plus %fs to print the output)"%(t1-t0, t2-t1)
    else:
        document = p.parse(f)
        print document
        print p.tree.testSerializer(document)
        if opts.error:
            print "\nParse errors:\n" + "\n".join(p.errors)

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

    return parser

if __name__ == "__main__":
    print os.path.abspath(os.curdir)
    parse()
