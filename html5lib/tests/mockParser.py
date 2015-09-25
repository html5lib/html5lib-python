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

from __future__ import absolute_import, division, unicode_literals

import sys
import os

if __name__ == '__main__':
    # Allow us to import from the src directory
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

from html5lib.tokenizer import HTMLTokenizer


class HTMLParser(object):
    """ Fake parser to test tokenizer output """
    def parse(self, stream, output=True):
        tokenizer = HTMLTokenizer(stream)
        for token in tokenizer:
            if output:
                print(token)

if __name__ == "__main__":
    x = HTMLParser()
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            import hotshot
            import hotshot.stats
            prof = hotshot.Profile('stats.prof')
            prof.runcall(x.parse, sys.argv[1], False)
            prof.close()
            stats = hotshot.stats.load('stats.prof')
            stats.strip_dirs()
            stats.sort_stats('time')
            stats.print_stats()
        else:
            x.parse(sys.argv[1])
    else:
        print("""Usage: python mockParser.py filename [stats]
        If stats is specified the hotshots profiler will run and output the
        stats instead.
        """)
