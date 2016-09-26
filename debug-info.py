# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function, unicode_literals

import platform
import sys


info = {
    "impl": platform.python_implementation(),
    "version": platform.python_version(),
    "revision": platform.python_revision(),
    "maxunicode": sys.maxunicode,
    "maxsize": sys.maxsize
}

search_modules = ["chardet", "datrie", "genshi", "html5lib", "lxml", "six"]
found_modules = []

for m in search_modules:
    try:
        __import__(m)
    except ImportError:
        pass
    else:
        found_modules.append(m)

info["modules"] = ", ".join(found_modules)


print("""html5lib debug info:

Python %(version)s (revision: %(revision)s)
Implementation: %(impl)s

sys.maxunicode: %(maxunicode)X
sys.maxsize: %(maxsize)X

Installed modules: %(modules)s""" % info)
