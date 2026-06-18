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
"""Unit tests for the dependency-graph drawing widget (widgets.graph_widget).

The shape helpers and the on_draw render path are exercised against an
in-memory cairo surface (no realized window). The motion-notify and
show-clicked handlers need a realized window / window action group and are out
of scope here. Relevant to issue #182.
"""
import cairo
import pytest

from gi.repository import GLib

from dtool_lookup_gui.widgets.graph_widget import (
    DtoolGraphWidget,
    circle,
    square,
    triangle,
)
from dtool_lookup_gui.models.simple_graph import SimpleGraph


def _surface_context():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
    return cairo.Context(surface)


def _graph_with_all_kinds():
    graph = SimpleGraph()
    graph.add_vertex(uuid="u-root", name="root", kind="root")
    graph.add_vertex(uuid="u-dep", name="dep", kind="dependent")
    graph.add_vertex(uuid="u-missing", name="missing", kind="does-not-exist")
    graph.add_edge(1, 0)
    graph.add_edge(2, 0)
    return graph


@pytest.fixture
def widget():
    w = DtoolGraphWidget()
    yield w
    # The graph setter installs a GLib timeout; remove it so it does not leak
    # into the shared default main context used by other tests.
    if w._timer is not None:
        GLib.source_remove(w._timer)
        w._timer = None


# --- shape helpers ---------------------------------------------------------

def test_shape_helpers_emit_paths():
    context = _surface_context()
    circle(context, 0.0, 0.0)
    square(context, 1.0, 1.0)
    triangle(context, 2.0, 2.0)
    # A path has been built; copying it must not raise.
    assert context.copy_path() is not None


# --- properties ------------------------------------------------------------

def test_search_by_uuid_round_trip(widget):
    assert widget.search_by_uuid is None

    def search(uuid):
        return uuid

    widget.search_by_uuid = search
    assert widget.search_by_uuid is search


def test_setting_graph_initializes_layout_and_state(widget):
    graph = _graph_with_all_kinds()
    widget.graph = graph
    assert widget.graph is graph
    assert widget._layout is not None
    assert widget._layout.positions.shape == (3, 2)
    # A per-vertex 'state' flag is initialized.
    assert len(graph.get_vertex_properties("state")) == 3


# --- drawing ---------------------------------------------------------------

def test_on_draw_without_graph_is_noop(widget):
    # No graph set yet -> early return, no error.
    widget.on_draw(widget, _surface_context())


def test_on_draw_renders_all_vertex_kinds_and_edges(widget):
    widget.graph = _graph_with_all_kinds()
    widget.on_draw(widget, _surface_context())


def test_on_draw_renders_highlighted_vertex(widget):
    graph = _graph_with_all_kinds()
    widget.graph = graph
    # Mark one vertex active to exercise the highlighted (stroked) branch.
    graph.set_vertex_properties("state", [True, False, False])
    widget.on_draw(widget, _surface_context())


# --- misc handlers ---------------------------------------------------------

def test_on_realize_is_noop(widget):
    widget.on_realize(widget)


def test_on_timeout_iterates_layout_and_reschedules(widget):
    widget.graph = _graph_with_all_kinds()
    # Returns True so the GLib timeout keeps firing.
    assert widget.on_timeout(widget) is True


def test_on_timeout_swallows_layout_errors(widget):
    class BadLayout:
        def iterate(self):
            raise RuntimeError("boom")

    widget._layout = BadLayout()
    # Errors during a layout step are logged, not raised, and the timeout
    # keeps rescheduling.
    assert widget.on_timeout(widget) is True
