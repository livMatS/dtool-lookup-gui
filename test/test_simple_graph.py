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
"""Unit tests for the dependency-graph model (models.simple_graph).

SimpleGraph is a plain vertex/edge container; GraphLayout runs a FIRE-based
force optimization over it. Both are pure NumPy/SciPy with no GTK dependency.
Layout positions are deterministic (grid initialization, no randomness), so the
results are reproducible. Relevant to issue #182.
"""
import numpy as np
import pytest

from dtool_lookup_gui.models.simple_graph import SimpleGraph, GraphLayout


def _make_graph(nb_vertices, edges=()):
    g = SimpleGraph()
    for i in range(nb_vertices):
        g.add_vertex(label=f"v{i}")
    for i, j in edges:
        g.add_edge(i, j)
    return g


# ===========================================================================
# SimpleGraph
# ===========================================================================

def test_empty_graph_has_no_vertices_or_edges():
    g = SimpleGraph()
    assert g.nb_vertices == 0
    assert g.nb_edges == 0
    assert g.vertex_properties == []
    assert list(g.edges) == []


def test_add_vertex_returns_index_and_stores_properties():
    g = SimpleGraph()
    assert g.add_vertex(name="a") == 0
    assert g.add_vertex(name="b") == 1
    assert g.nb_vertices == 2
    assert g.vertex_properties == [{"name": "a"}, {"name": "b"}]


def test_add_edge_records_endpoints():
    g = _make_graph(3, [(0, 1), (1, 2)])
    assert g.vertex1 == [0, 1]
    assert g.vertex2 == [1, 2]
    assert g.nb_edges == 2
    assert list(g.edges) == [(0, 1), (1, 2)]


@pytest.mark.parametrize("i,j", [(None, 0), (0, None), (-1, 0), (0, 3), (3, 0)])
def test_add_edge_rejects_out_of_bounds(i, j):
    g = _make_graph(3)
    with pytest.raises(ValueError):
        g.add_edge(i, j)


def test_set_and_get_vertex_properties_round_trip():
    g = _make_graph(3)
    g.set_vertex_properties("color", ["red", "green", "blue"])
    assert g.get_vertex_properties("color") == ["red", "green", "blue"]


def test_set_vertex_properties_stops_at_shortest():
    # zip() stops at the shorter sequence, so a short list updates a prefix.
    g = _make_graph(3)
    g.set_vertex_properties("rank", [1, 2])
    assert g.get_vertex_properties("label") == ["v0", "v1", "v2"]
    assert g.vertex_properties[0]["rank"] == 1
    assert g.vertex_properties[1]["rank"] == 2
    assert "rank" not in g.vertex_properties[2]


# ===========================================================================
# GraphLayout
# ===========================================================================

def test_layout_produces_one_position_per_vertex():
    g = _make_graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)])
    layout = GraphLayout(g)
    assert layout.graph is g
    assert layout.positions.shape == (5, 2)
    assert np.all(np.isfinite(layout.positions))


def test_layout_single_vertex_is_stable():
    # Exercises the nb_vertices <= 1 early-return branches in the force terms.
    g = _make_graph(1)
    layout = GraphLayout(g)
    assert layout.positions.shape == (1, 2)
    assert np.all(np.isfinite(layout.positions))


def test_layout_without_edges_only_has_repulsion():
    g = _make_graph(4)
    layout = GraphLayout(g)
    assert layout.positions.shape == (4, 2)
    assert np.all(np.isfinite(layout.positions))


def test_layout_iterate_keeps_positions_finite():
    g = _make_graph(4, [(0, 1), (1, 2), (2, 3)])
    layout = GraphLayout(g, init_iter=5)
    before = layout.positions.copy()
    layout.iterate()
    assert layout.positions.shape == before.shape
    assert np.all(np.isfinite(layout.positions))


def test_layout_relaxes_connected_pair_towards_equilibrium():
    # Two connected vertices should settle near the spring equilibrium distance.
    g = _make_graph(2, [(0, 1)])
    layout = GraphLayout(g, equilibrium_distance=2.0, init_iter=300)
    distance = np.linalg.norm(layout.positions[0] - layout.positions[1])
    assert distance == pytest.approx(2.0, abs=0.5)
