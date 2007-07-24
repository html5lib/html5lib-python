import unittest

from html5lib.filters.formfiller import SimpleFilter

class FieldStorage(dict):
    def getlist(self, name):
        l = self[name]
        if isinstance(l, list):
            return l
        elif isinstance(l, tuple) or hasattr(l, '__iter__'):
            return list(l)
        return [l]

class TestCase(unittest.TestCase):
    def runTest(self, input, formdata, expected):
        output = list(SimpleFilter(input, formdata))
        errorMsg = "\n".join(["\n\nInput:", str(input),
                              "\nForm data:", str(formdata),
                              "\nExpected:", str(expected),
                              "\nReceived:", str(output)])
        self.assertEquals(output, expected, errorMsg)

    def testSingleTextInputWithValue(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"text"), (u"name", u"foo"), (u"value", u"quux")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"text"), (u"name", u"foo"), (u"value", u"bar")]}])

    def testSingleTextInputWithoutValue(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"text"), (u"name", u"foo")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"text"), (u"name", u"foo"), (u"value", u"bar")]}])

    def testSingleCheckbox(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"bar")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"bar"), (u"checked", u"")]}])

    def testSingleCheckboxShouldBeUnchecked(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"quux")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"quux")]}])

    def testSingleCheckboxCheckedByDefault(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"bar"), (u"checked", u"")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"bar"), (u"checked", u"")]}])

    def testSingleCheckboxCheckedByDefaultShouldBeUnchecked(self):
        self.runTest(
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"quux"), (u"checked", u"")]}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"EmptyTag", "name": u"input",
                "data": [(u"type", u"checkbox"), (u"name", u"foo"), (u"value", u"quux")]}])

    def testSingleTextareaWithValue(self):
        self.runTest(
            [{"type": u"StartTag", "name": u"textarea", "data": [(u"name", u"foo")]},
             {"type": u"Characters", "data": u"quux"},
             {"type": u"EndTag", "name": u"textarea", "data": []}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"StartTag", "name": u"textarea", "data": [(u"name", u"foo")]},
             {"type": u"Characters", "data": u"bar"},
             {"type": u"EndTag", "name": u"textarea", "data": []}])

    def testSingleTextareaWithoutValue(self):
        self.runTest(
            [{"type": u"StartTag", "name": u"textarea", "data": [(u"name", u"foo")]},
             {"type": u"EndTag", "name": u"textarea", "data": []}],
            FieldStorage({"foo": "bar"}),
            [{"type": u"StartTag", "name": u"textarea", "data": [(u"name", u"foo")]},
             {"type": u"Characters", "data": u"bar"},
             {"type": u"EndTag", "name": u"textarea", "data": []}])

def main():
    unittest.main()

if __name__ == "__main__":
    main()
