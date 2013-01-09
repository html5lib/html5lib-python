
class Filter(object):
    def __init__(self, source):
        self.source = source
    __init__.func_annotations = {}

    def __iter__(self):
        return iter(self.source)
    __iter__.func_annotations = {}

    def __getattr__(self, name):
        return getattr(self.source, name)
    __getattr__.func_annotations = {}
