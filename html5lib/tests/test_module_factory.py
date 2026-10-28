from __future__ import absolute_import, division, unicode_literals

from types import ModuleType
import xml.etree.ElementTree as ElementTree

import pytest

from html5lib import HTMLParser, getTreeBuilder
from html5lib._utils import moduleFactoryFactory


def _module_factory():
    def factory(backend, *args, **kwargs):
        return {"backend": backend, "arguments": args, "options": kwargs}

    return moduleFactoryFactory(factory)


@pytest.mark.parametrize("args_a, options_a, args_b, options_b", [
    (("first",), {}, ("second",), {}),
    ((), {"enabled": False}, (), {"enabled": True}),
    (("first",), {"enabled": False}, ("first",), {"enabled": True}),
    (("first",), {"enabled": False}, ("second",), {"enabled": False}),
], ids=["positional", "keyword", "shared-arguments", "shared-options"])
def test_module_factory_reuses_each_configuration(args_a, options_a, args_b, options_b):
    backend = ModuleType(str("factory_backend"))
    build = _module_factory()

    first = build(backend, *args_a, **options_a)
    second = build(backend, *args_b, **options_b)
    first_again = build(backend, *args_a, **options_a)
    second_again = build(backend, *args_b, **options_b)

    assert first.backend is backend
    assert second.backend is backend
    assert first.arguments == args_a
    assert second.arguments == args_b
    assert first.options == options_a
    assert second.options == options_b
    assert first_again.arguments == args_a
    assert first_again.options == options_a
    assert second_again.arguments == args_b
    assert second_again.options == options_b
    assert first is not second
    assert first_again is first
    assert second_again is second


def test_module_factory_keeps_distinct_backends_cached():
    backend_a = ModuleType(str("factory_backend_a"))
    backend_b = ModuleType(str("factory_backend_b"))
    build = _module_factory()

    first = build(backend_a, enabled=True)
    second = build(backend_b, enabled=True)

    assert first.backend is backend_a
    assert second.backend is backend_b
    assert first is not second
    assert build(backend_a, enabled=True) is first
    assert build(backend_b, enabled=True) is second


@pytest.mark.parametrize("full_tree", [False, True])
def test_etree_builder_identity_survives_alternating_options(full_tree):
    first = getTreeBuilder("etree", ElementTree, fullTree=full_tree)
    first_parser = HTMLParser(tree=first, namespaceHTMLElements=False)
    second = getTreeBuilder("etree", ElementTree, fullTree=not full_tree)
    second_parser = HTMLParser(tree=second, namespaceHTMLElements=False)
    first_again = getTreeBuilder("etree", ElementTree, fullTree=full_tree)
    second_again = getTreeBuilder("etree", ElementTree, fullTree=not full_tree)

    assert first.implementation is ElementTree
    assert second.implementation is ElementTree
    assert first is not second
    assert first_again is first
    assert second_again is second
    assert isinstance(first_parser.tree, first_again)
    assert isinstance(second_parser.tree, second_again)

    # Parsing is an existing-behavior control, not the cache regression itself.
    parsers = [(first_parser, full_tree), (second_parser, not full_tree)]
    for parser, includes_document in parsers:
        document = parser.parse("<p>content</p>")
        root = document.find("html") if includes_document else document
        assert root.tag == "html"
        assert root.find("body/p").text == "content"
