"""
 Usage:
   python parse.py tests/sites/web-apps.htm > outputfile
     To parse the file web-apps.htm and get a tree.
   
   python parse.py tests/sites/web-apps.htm x > outputfile
     To parse the file web-apps.htm and get a profile.
"""
import sys
import os

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

if __name__ == "__main__":
    p = parser.HTMLParser()
    if len(sys.argv) > 1:
        x = sys.argv[1]
        if len(sys.argv) > 2:
            import hotshot
            import hotshot.stats
            prof = hotshot.Profile('stats.prof')
            prof.runcall(p.parse, x, False)
            prof.close()
            stats = hotshot.stats.load('stats.prof')
            stats.strip_dirs()
            stats.sort_stats('time')
            stats.print_stats()
        else:
            from time import time
            t = time()
            document = p.parse(x)
            t = time() - t
            t2 = time()
            print convertTreeDump(document.printTree())
            t2 = time() - t2
            print "\n\nDuration:", t, "\nTree dump duration:", t2
    else:
        print """Pass one argument to parse the document and two to get an
              indication on what's going on.
              """
