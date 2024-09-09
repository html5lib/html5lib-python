#!/usr/bin/env python

"""
usage: toxver.py [python-version] [deps]

Returns a Tox environment name given a GHA matrix Python version and dependencies.
Many GHA configurations do this with inline Bash scripts but we want our solution
to be cross-platform and work on Windows workers, too.

Examples:

    $ toxver.py pypy-3.8 base
    TOXENV=pypy3-base

    $ toxver.py ~3.12.0-0 optional
    TOXENV=py312-optional

"""


import sys


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 1

    deps = argv[2]

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
