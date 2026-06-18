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
"""Unit tests for the SearchState client model (pagination/sorting/search)."""
import pytest

from dtool_lookup_gui.models.search_state import SearchState


@pytest.fixture
def state():
    return SearchState()


# --- defaults and resets ---------------------------------------------------

def test_defaults(state):
    assert state.search_text == ""
    assert state.page_size == 10
    assert state.current_page == 1
    assert state.last_page == 1
    assert state.total_pages == 1
    assert state.total_number_of_entries == 0
    assert state.sort_fields == ["uri"]
    assert state.sort_order == [1]
    assert state.fetching_results is False


def test_reset_pagination(state):
    state.last_page = 9
    state._current_page = 4
    state.reset_pagination()
    assert state.current_page == 1
    assert state.last_page == 1


def test_reset_sorting(state):
    state.sort_fields = ["name"]
    state.sort_order = [-1]
    state.reset_sorting()
    assert state.sort_fields == ["uri"]
    assert state.sort_order == [1]


# --- search text -----------------------------------------------------------

def test_search_text_round_trip(state):
    state.search_text = "toluene"
    assert state.search_text == "toluene"


# --- current_page clamping -------------------------------------------------

def test_current_page_clamped_to_minimum(state):
    state.current_page = 0
    assert state.current_page == 1


def test_current_page_clamped_to_last_page(state):
    state.last_page = 5
    state.current_page = 99
    assert state.current_page == 5


def test_current_page_accepts_value_in_range(state):
    state.last_page = 5
    state.current_page = 3
    assert state.current_page == 3


# --- page-bound validation -------------------------------------------------

@pytest.mark.parametrize("setter", ["last_page", "first_page", "page_size"])
def test_positive_int_setters_reject_invalid(state, setter):
    with pytest.raises(ValueError):
        setattr(state, setter, 0)
    with pytest.raises(ValueError):
        setattr(state, setter, "x")


def test_page_size_round_trip(state):
    state.page_size = 50
    assert state.page_size == 50


def test_fetching_results_requires_bool(state):
    state.fetching_results = True
    assert state.fetching_results is True
    with pytest.raises(ValueError):
        state.fetching_results = "yes"


# --- sort fields -----------------------------------------------------------

def test_sort_fields_accepts_single_string(state):
    state.sort_fields = "name"
    assert state.sort_fields == ["name"]


def test_sort_fields_rejects_non_list(state):
    with pytest.raises(ValueError):
        state.sort_fields = 5


def test_sort_fields_rejects_unknown_field(state):
    with pytest.raises(ValueError):
        state.sort_fields = ["not_a_field"]


# --- sort order ------------------------------------------------------------

def test_sort_order_accepts_single_int(state):
    # sort_fields defaults to one field, so a single-element order is valid.
    state.sort_order = 1
    assert state.sort_order == [1]


def test_sort_order_rejects_non_list(state):
    with pytest.raises(ValueError):
        state.sort_order = "asc"


def test_sort_order_length_must_match_sort_fields(state):
    state.sort_fields = ["name", "uri"]
    with pytest.raises(ValueError):
        state.sort_order = [1]


# --- ingest helpers --------------------------------------------------------

def test_ingest_pagination_information(state):
    state.ingest_pagination_information(
        {"total": 284, "total_pages": 29, "first_page": 1, "last_page": 29, "page": 3})
    assert state.first_page == 1
    assert state.last_page == 29
    assert state.current_page == 3
    assert state.total_pages == 29
    assert state.total_number_of_entries == 284


def test_ingest_pagination_information_uses_defaults_when_empty(state):
    state.ingest_pagination_information({})
    assert state.first_page == 1
    assert state.last_page == 1
    assert state.current_page == 1
    assert state.total_number_of_entries == 0


def test_ingest_sorting_information(state):
    state.ingest_sorting_information({"sort": {"base_uri": 1, "name": -1}})
    assert state.sort_fields == ["base_uri", "name"]
    assert state.sort_order == [1, -1]


# --- next/previous page navigation -----------------------------------------

def test_next_page_increments_within_bounds(state):
    state.last_page = 5
    state.current_page = 2
    assert state.next_page == 3


def test_next_page_caps_at_last_page(state):
    state.last_page = 5
    state.current_page = 5
    assert state.next_page == 5


def test_previous_page_decrements_within_bounds(state):
    state.last_page = 5
    state.current_page = 3
    assert state.previous_page == 2


def test_previous_page_floors_at_first_page(state):
    state.last_page = 5
    state.current_page = 1
    assert state.previous_page == 1
