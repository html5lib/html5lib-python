import sys
import os
import glob
import StringIO
import unittest
import new

import parser

#Allow us to import the parent module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.pardir))

def testParser(testString):
    testString = testString.split("\n")
    assert testString[0] == "#data"
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        if line[0] != "#":
            if currentList == output:
                assert line[0] == "|"
                currentList.append(line[1:])
            else:
                currentList.append(line)
        elif line == "#errors":
            assert input
            currentList = errors
        elif line == "#document":
            assert input
            currentList = output
    return input, output, errors
