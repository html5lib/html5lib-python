
from test_parser import *
import sys, os

os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))


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
