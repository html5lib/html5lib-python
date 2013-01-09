from __future__ import absolute_import
import sys
import os
import json
import re

import html5lib
from . import support
from . import test_parser
from . import test_tokenizer
from io import open

p = html5lib.HTMLParser()

unnamespaceExpected = re.compile(ur"^(\|\s*)<html ([^>]+)>", re.M).sub

def main(out_path):
    if not os.path.exists(out_path):
        sys.stderr.write(u"Path %s does not exist"%out_path)
        sys.exit(1)

    for filename in support.get_data_files(u'tokenizer', u'*.test'):
        run_file(filename, out_path)
main.func_annotations = {}

def run_file(filename, out_path):
    try:
        tests_data = json.load(file(filename))
    except ValueError:
        sys.stderr.write(u"Failed to load %s\n"%filename)
        return
    name = os.path.splitext(os.path.split(filename)[1])[0]
    output_file = open(os.path.join(out_path, u"tokenizer_%s.dat"%name), u"w")

    if u'tests' in tests_data:
        for test_data in tests_data[u'tests']:
            if u'initialStates' not in test_data:
                test_data[u"initialStates"] = [u"Data state"]
                
            for initial_state in test_data[u"initialStates"]:
                if initial_state != u"Data state":
                    #don't support this yet
                    continue
                test = make_test(test_data)
                output_file.write(test)

    output_file.close()
run_file.func_annotations = {}

def make_test(test_data):
    if u'doubleEscaped' in test_data:
        test_data = test_tokenizer.unescape_test(test_data)

    rv = []
    rv.append(u"#data")
    rv.append(test_data[u"input"].encode(u"utf8"))
    rv.append(u"#errors")
    tree = p.parse(test_data[u"input"])
    output = p.tree.testSerializer(tree)
    output  = u"\n".join((u"| "+ line[3:]) if line.startswith(u"|  ") else line
                        for line in output.split(u"\n"))
    output = unnamespaceExpected(ur"\1<\2>", output)
    rv.append(output.encode(u"utf8"))
    rv.append(u"")
    return u"\n".join(rv)
make_test.func_annotations = {}

if __name__ == u"__main__":
    main(sys.argv[1])
