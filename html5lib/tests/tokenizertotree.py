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
import json
import re

import html5lib
from . import support
from . import test_tokenizer

p = html5lib.HTMLParser()

unnamespaceExpected = re.compile(r"^(\|\s*)<html ([^>]+)>", re.M).sub


def main(out_path):
    if not os.path.exists(out_path):
        sys.stderr.write("Path %s does not exist" % out_path)
        sys.exit(1)

    for filename in support.get_data_files('tokenizer', '*.test'):
        run_file(filename, out_path)


def run_file(filename, out_path):
    try:
        tests_data = json.load(open(filename, "r"))
    except ValueError:
        sys.stderr.write("Failed to load %s\n" % filename)
        return
    name = os.path.splitext(os.path.split(filename)[1])[0]
    output_file = open(os.path.join(out_path, "tokenizer_%s.dat" % name), "w")

    if 'tests' in tests_data:
        for test_data in tests_data['tests']:
            if 'initialStates' not in test_data:
                test_data["initialStates"] = ["Data state"]

            for initial_state in test_data["initialStates"]:
                if initial_state != "Data state":
                    # don't support this yet
                    continue
                test = make_test(test_data)
                output_file.write(test)

    output_file.close()


def make_test(test_data):
    if 'doubleEscaped' in test_data:
        test_data = test_tokenizer.unescape_test(test_data)

    rv = []
    rv.append("#data")
    rv.append(test_data["input"].encode("utf8"))
    rv.append("#errors")
    tree = p.parse(test_data["input"])
    output = p.tree.testSerializer(tree)
    output = "\n".join(("| " + line[3:]) if line.startswith("|  ") else line
                       for line in output.split("\n"))
    output = unnamespaceExpected(r"\1<\2>", output)
    rv.append(output.encode("utf8"))
    rv.append("")
    return "\n".join(rv)

if __name__ == "__main__":
    main(sys.argv[1])
