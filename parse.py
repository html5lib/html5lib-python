"""usage: %prog [options] filename

Parse a document to a DOMlite tree, with optional profiling
"""

import sys
import os
from optparse import OptionParser

from src import parser

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

    p = parser.HTMLParser()
    # Don't try to open args[0]. It should be possible to pass a string or file
    # reference. HTMLInputStream takes care of the difference.
    f = args[0]
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
        print convertTreeDump(document.printTree())
        t2 = time.time()
        print "\n\nRun took: %fs (plus %fs to print the output)"%(t1-t0, t2-t1)
    else:
        document = p.parse(f)
        print convertTreeDump(document.printTree())
        print "\nParse errors:\n" + "\n".join(p.errors)

def getOptParser():
    parser = OptionParser(usage=__doc__)

    parser.add_option("-p", "--profile", action="store_true", default=False,
                      dest="profile", help="Use the hotdhot profiler to "
                      "produce a detailed log of the run")

    parser.add_option("-t", "--time",
                      action="store_true", default=False, dest="time",
                      help="Time the run using time.time (may not be accurate on all platforms, especially for short runs)")

    return parser

if __name__ == "__main__":
    print os.path.abspath(os.curdir)
    parse()
