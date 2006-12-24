import sys
import os

from src import parser

def convertTreeDump(treedump):
    """convert the output of str(document) to something more readable
    """
    treedump = treedump.split("\n")[1:]
    rv = []
    for line in treedump:
        rv.append(line[3:])
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
            document = p.parse(x)
            print convertTreeDump(document.printTree())
    else:
        print """Pass one argument to parse the document and two to get an
              indication on what's going on.
              """
