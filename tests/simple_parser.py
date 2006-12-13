from test_parser import *
import sys
os.chdir("..")
import parser

if __name__ == "__main__":
    x = ""
    if len(sys.argv) > 1:
        x = sys.argv[1]
    else:
        x = "x"
    p = parser.HTMLParser()
    document = p.parse(StringIO.StringIO(x))
    print convertTreeDump(document.printTree())
