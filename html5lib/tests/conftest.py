import os.path

from .tree_construction import TreeConstructionFile

_dir = os.path.abspath(os.path.dirname(__file__))
_testdata = os.path.join(_dir, "testdata")
_tree_construction = os.path.join(_testdata, "tree-construction")


def pytest_collectstart():
    """check to see if the git submodule has been init'd"""
    pass


def pytest_collect_file(path, parent):
    dir = os.path.abspath(path.dirname)
    if dir == _tree_construction:
        if path.basename == "template.dat":
            return
        if path.ext == ".dat":
            return TreeConstructionFile(path, parent)
