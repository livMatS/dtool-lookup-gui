#
# Copyright 2026 Johannes Laurin Hörmann
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""Unit tests for the module-level helper functions in dtool_lookup_gui.__init__.

These are pure functions (UUID detection, timestamp/date conversion, README
tree-store population and YAML validation) that do not need the running
application; only fill_readme_tree_store touches a Gtk.TreeStore. The GTK env
isolation (busless D-Bus, in-memory GSettings) is set up by test/conftest.py.
"""
import datetime

import pytest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from dtool_lookup_gui import (
    is_uuid,
    to_timestamp,
    datetime_to_string,
    date_to_string,
    fill_readme_tree_store,
    _validate_readme,
    _standardize_readme,
)

# A real UUID taken from the project's example administrative metadata.
EXAMPLE_UUID = "26785c2a-e8f8-46bf-82a1-cec92dbdf28f"

# README content that ruamel.yaml rejects: a duplicate mapping key raises
# DuplicateKeyError, one of the errors the helpers explicitly handle.
INVALID_README = "a: 1\na: 2\n"


# ---------------------------------------------------------------------------
# is_uuid
# ---------------------------------------------------------------------------

def test_is_uuid_accepts_valid_uuid():
    assert is_uuid(EXAMPLE_UUID) is True


@pytest.mark.parametrize("value", ["not-a-uuid", "12345", ""])
def test_is_uuid_rejects_non_uuid(value):
    assert is_uuid(value) is False


def test_is_uuid_coerces_non_string_input():
    # Non-string input is stringified before parsing, so this must not raise.
    assert is_uuid(12345) is False


# ---------------------------------------------------------------------------
# timestamp / date conversion
# ---------------------------------------------------------------------------

def test_datetime_to_string_from_numeric():
    result = datetime_to_string(0)
    assert isinstance(result, datetime.datetime)
    assert result == datetime.datetime.fromtimestamp(0)


def test_date_to_string_from_numeric():
    result = date_to_string(0)
    assert isinstance(result, datetime.date)
    assert result == datetime.date.fromtimestamp(0)


def test_datetime_to_string_parses_rfc_string():
    # to_timestamp parses the lookup server's RFC 1123 style strings.
    ts = to_timestamp("Wed, 11 May 2023 12:00:00 GMT")
    assert ts > 0
    assert datetime_to_string("Wed, 11 May 2023 12:00:00 GMT") == \
        datetime.datetime.fromtimestamp(ts)


# ---------------------------------------------------------------------------
# fill_readme_tree_store
# ---------------------------------------------------------------------------

def _new_store():
    # Columns: key, value-as-string, is_uuid flag, pango markup.
    return Gtk.TreeStore(str, str, bool, str)


def test_fill_readme_tree_store_none_data_is_noop():
    store = _new_store()
    fill_readme_tree_store(store, None)
    assert store.iter_n_children(None) == 0


def test_fill_readme_tree_store_flat_mapping():
    store = _new_store()
    fill_readme_tree_store(store, {"name": "test", "size": "19347"})
    assert store.iter_n_children(None) == 2


def test_fill_readme_tree_store_marks_uuid_with_markup():
    store = _new_store()
    fill_readme_tree_store(store, {"uuid": EXAMPLE_UUID})
    it = store.get_iter_first()
    assert store.get_value(it, 1) == EXAMPLE_UUID
    assert store.get_value(it, 2) is True
    assert 'foreground="blue"' in store.get_value(it, 3)


def test_fill_readme_tree_store_plain_value_not_marked():
    store = _new_store()
    fill_readme_tree_store(store, {"name": "test"})
    it = store.get_iter_first()
    assert store.get_value(it, 2) is False


def test_fill_readme_tree_store_nested_dict_and_list():
    store = _new_store()
    data = {"tags": ["a", "b"], "meta": {"k": "v"}}
    fill_readme_tree_store(store, data)
    # Two top-level keys, in insertion order.
    assert store.iter_n_children(None) == 2
    tags_it = store.get_iter_first()
    assert store.get_value(tags_it, 0) == "tags"
    assert store.iter_n_children(tags_it) == 2
    meta_it = store.iter_next(tags_it)
    assert store.get_value(meta_it, 0) == "meta"
    assert store.iter_n_children(meta_it) == 1


def test_fill_readme_tree_store_list_of_containers():
    store = _new_store()
    # Exercises the list branch that recurses into nested lists and dicts.
    data = {"items": [["nested"], {"key": "value"}]}
    fill_readme_tree_store(store, data)
    items_it = store.get_iter_first()
    assert store.iter_n_children(items_it) == 2


# ---------------------------------------------------------------------------
# _validate_readme / _standardize_readme
# ---------------------------------------------------------------------------

def test_validate_readme_returns_parsed_mapping_for_valid_yaml():
    data, error = _validate_readme("name: test\n")
    assert error is None
    assert data["name"] == "test"


def test_validate_readme_returns_error_for_invalid_yaml():
    data, error = _validate_readme(INVALID_README)
    assert data is None
    assert error is not None


def test_standardize_readme_formats_with_explicit_start():
    out = _standardize_readme("name: test\n")
    assert out.startswith("---")
    assert "name: test" in out


def test_standardize_readme_raises_value_error_on_invalid_yaml():
    with pytest.raises(ValueError):
        _standardize_readme(INVALID_README)
