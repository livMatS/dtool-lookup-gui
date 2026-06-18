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
"""Tests for DependencyGraph error handling — fixes #370 / #182.

When the lookup server returns a non-JSON response (HTML error page),
aiohttp raises ContentTypeError. The graph must remain empty and a
user-readable error must be logged (which surfaces in the GUI error bar).
"""
import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

from aiohttp import RequestInfo
from aiohttp.client_exceptions import ContentTypeError
from yarl import URL

from dtool_lookup_gui.utils.dependency_graph import DependencyGraph


def _make_content_type_error():
    """Construct a realistic ContentTypeError as aiohttp would raise it."""
    request_info = RequestInfo(
        url=URL("https://example.com/lookup/graph/uuids/abc"),
        method="GET",
        headers={},
        real_url=URL("https://example.com/lookup/graph/uuids/abc"),
    )
    return ContentTypeError(request_info, history=(), message="Attempt to decode JSON with unexpected mimetype: text/html")


@pytest.mark.asyncio
async def test_dependency_graph_content_type_error_on_first_page(caplog):
    """ContentTypeError on first page leaves graph empty and logs friendly message."""
    graph = DependencyGraph()
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(side_effect=_make_content_type_error())

    with caplog.at_level(logging.ERROR, logger="dtool_lookup_gui.utils.dependency_graph"):
        await graph.trace_dependencies(lookup, root_uuid="abc-123")

    # Graph must be empty — no vertices
    assert graph.graph.nb_vertices == 0

    # Error must have been logged with a user-readable message
    assert len(caplog.records) >= 1
    error_msg = caplog.records[-1].message
    assert "abc-123" in error_msg, "Error should mention the UUID"
    assert any(word in error_msg.lower() for word in ["unexpected", "html", "server", "json"]), \
        f"Error message should explain the problem, got: {error_msg!r}"


@pytest.mark.asyncio
async def test_dependency_graph_content_type_error_on_subsequent_page(caplog):
    """ContentTypeError on a subsequent page also logs a friendly message."""
    graph = DependencyGraph()

    # First page succeeds with one dataset and pagination info indicating 2 pages
    first_page_dataset = {
        "uuid": "abc-123",
        "name": "root-dataset",
    }

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: return data and set pagination via out-param
            pagination = kwargs.get("pagination", {})
            pagination.update({"total": 20, "page_size": 10, "page": 1,
                               "first_page": 1, "last_page": 2,
                               "total_pages": 2})
            return [first_page_dataset]
        else:
            raise _make_content_type_error()

    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(side_effect=side_effect)

    with caplog.at_level(logging.ERROR, logger="dtool_lookup_gui.utils.dependency_graph"):
        await graph.trace_dependencies(lookup, root_uuid="abc-123")

    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) >= 1
    error_msg = error_records[-1].message
    assert any(word in error_msg.lower() for word in ["unexpected", "html", "server", "json"]), \
        f"Error message should explain the problem, got: {error_msg!r}"


@pytest.mark.asyncio
async def test_dependency_graph_success_builds_graph():
    """Sanity check: successful response builds the graph correctly."""
    graph = DependencyGraph()

    datasets = [
        {"uuid": "root-uuid", "name": "root"},
        {"uuid": "child-uuid", "name": "child", "derived_from": ["root-uuid"]},
    ]
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(return_value=datasets)

    await graph.trace_dependencies(lookup, root_uuid="root-uuid")

    assert graph.graph.nb_vertices == 2
    uuids = {v["uuid"] for v in graph.graph.vertex_properties}
    assert "root-uuid" in uuids
    assert "child-uuid" in uuids


# Valid UUIDs are required for edges: trace_dependencies only links a child to a
# parent when the parent identifier passes is_uuid().
ROOT = "11111111-1111-1111-1111-111111111111"
CHILD = "22222222-2222-2222-2222-222222222222"
MISSING = "33333333-3333-3333-3333-333333333333"


@pytest.mark.asyncio
async def test_edge_built_between_existing_datasets():
    graph = DependencyGraph()
    datasets = [
        {"uuid": ROOT, "name": "root"},
        {"uuid": CHILD, "name": "child", "derived_from": [ROOT]},
    ]
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(return_value=datasets)

    await graph.trace_dependencies(lookup, root_uuid=ROOT)

    assert graph.graph.nb_vertices == 2
    assert graph.graph.nb_edges == 1
    assert graph.missing_uuids == []


@pytest.mark.asyncio
async def test_missing_parent_added_as_placeholder_vertex():
    graph = DependencyGraph()
    datasets = [
        {"uuid": CHILD, "name": "child", "derived_from": [MISSING]},
    ]
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(return_value=datasets)

    await graph.trace_dependencies(lookup, root_uuid=CHILD)

    assert MISSING in graph.missing_uuids
    assert graph.graph.nb_vertices == 2  # child plus the missing placeholder
    assert graph.graph.nb_edges == 1
    kinds = {v["uuid"]: v["kind"] for v in graph.graph.vertex_properties}
    assert kinds[MISSING] == "does-not-exist"


@pytest.mark.asyncio
async def test_multi_page_results_are_extended():
    graph = DependencyGraph()
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            pagination = kwargs.get("pagination", {})
            pagination.update({"total": 2, "page_size": 1, "page": 1,
                               "first_page": 1, "last_page": 2, "total_pages": 2})
            return [{"uuid": ROOT, "name": "root"}]
        return [{"uuid": CHILD, "name": "child", "derived_from": [ROOT]}]

    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(side_effect=side_effect)

    await graph.trace_dependencies(lookup, root_uuid=ROOT)

    assert call_count == 2
    assert graph.graph.nb_vertices == 2
    assert graph.graph.nb_edges == 1


@pytest.mark.asyncio
async def test_invalid_dependency_keys_are_ignored():
    graph = DependencyGraph()
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(return_value=[])

    # An int is neither a JSON string nor a list -> coerced to None with a warning.
    await graph.trace_dependencies(lookup, root_uuid=ROOT, dependency_keys=123)

    _, kwargs = lookup.get_graph_by_uuid.call_args
    assert kwargs["dependency_keys"] is None


@pytest.mark.asyncio
async def test_dependency_keys_json_string_is_parsed():
    graph = DependencyGraph()
    lookup = MagicMock()
    lookup.get_graph_by_uuid = AsyncMock(return_value=[])

    await graph.trace_dependencies(
        lookup, root_uuid=ROOT, dependency_keys='["readme.derived_from.uuid"]')

    _, kwargs = lookup.get_graph_by_uuid.call_args
    assert kwargs["dependency_keys"] == ["readme.derived_from.uuid"]
