#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys


def main(argv):
    if len(argv) != 3:
        print("usage: toxver.py [python-version] [deps]", file=sys.stderr)
        return 1

    deps = argv[2]

    if argv[1].startswith("pypy-2"):
        print("TOXENV=pypy-" + deps)
        return 0

    if argv[1].startswith("pypy-3"):
        print("TOXENV=pypy3-" + deps)
        return 0

    if argv[1].startswith("~"):
        ver = argv[1][1:5]
    else:
        ver = argv[1]

    ver = ver.replace(".", "")
    print("TOXENV=py" + ver + "-" + deps)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
