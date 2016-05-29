import os.path

from .tree_construction import TreeConstructionFile
from .tokenizer import TokenizerFile
from .sanitizer import SanitizerFile

_dir = os.path.abspath(os.path.dirname(__file__))
_testdata = os.path.join(_dir, "testdata")
_tree_construction = os.path.join(_testdata, "tree-construction")
_tokenizer = os.path.join(_testdata, "tokenizer")
_sanitizer_testdata = os.path.join(_dir, "sanitizer-testdata")


def pytest_collectstart():
    """check to see if the git submodule has been init'd"""
    pass


def pytest_collect_file(path, parent):
    dir = os.path.abspath(path.dirname)
    dir_and_parents = set()
    while dir not in dir_and_parents:
        dir_and_parents.add(dir)
        dir = os.path.dirname(dir)

    if _tree_construction in dir_and_parents:
        if path.ext == ".dat":
            return TreeConstructionFile(path, parent)
    elif _tokenizer in dir_and_parents:
        if path.ext == ".test":
            return TokenizerFile(path, parent)
    elif _sanitizer_testdata in dir_and_parents:
        if path.ext == ".dat":
            return SanitizerFile(path, parent)
