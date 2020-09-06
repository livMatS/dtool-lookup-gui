#
# Copyright 2020 Lars Pastewka
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

import numpy as np


class SimpleGraph:
    def __init__(self):
        self._vertex_properties = []
        self._vertex1 = []
        self._vertex2 = []

    @property
    def nb_vertices(self):
        return len(self._vertex_properties)

    @property
    def vertex_properties(self):
        return self._vertex_properties

    @property
    def vertex1(self):
        return self._vertex1

    @property
    def vertex2(self):
        return self._vertex2

    @property
    def edges(self):
        return zip(self._vertex1, self._vertex2)

    @property
    def nb_edges(self):
        return len(self.vertex1)

    def add_vertex(self, **kwargs):
        self._vertex_properties += [kwargs]
        return len(self._vertex_properties) - 1

    def add_edge(self, i, j):
        nb_vertices = self.nb_vertices
        if i is None or i < 0 or i >= nb_vertices:
            raise ValueError(f'Vertex index {i} out of bounds 0 to '
                             f'{nb_vertices}.')
        if j is None or j < 0 or j >= nb_vertices:
            raise ValueError(f'Vertex index {j} out of bounds 0 to '
                             f'{nb_vertices}.')
        self._vertex1 += [i]
        self._vertex2 += [j]

    def set_vertex_properties(self, name, properties):
        for vertex, property in zip(self._vertex_properties, properties):
            vertex[name] = property

    def get_vertex_properties(self, name):
        properties = []
        for vertex in self._vertex_properties:
            properties += [vertex[name]]
        return properties


class GraphLayout:
    def __init__(self, graph, spring_constant=1, equilibrium_distance=1):
        self.graph = graph
        self.spring_constant = spring_constant
        self.equilibrium_distance = equilibrium_distance

        self._initialize_positions()

    @property
    def positions(self):
        return self._positions

    def _initialize_positions(self):
        nb_vertices = self.graph.nb_vertices
        n = int(np.sqrt(nb_vertices)) + 1
        grid = (np.mgrid[:n, :n].T).reshape(-1, 2)[:nb_vertices]
        self._positions = grid.astype(float) * self.equilibrium_distance

    def _energy(self, pos):
        i = np.array(self.graph.vertex1)
        j = np.array(self.graph.vertex2)
        distance = np.sqrt(np.sum((pos[i] - pos[j]) ** 2, axis=1))
        return 0.5 * self.spring_constant * (
                distance - self.equilibrium_distance) ** 2

    def _forces(self, pos):
        i = np.array(self.graph.vertex1)
        j = np.array(self.graph.vertex2)
        distance = np.sqrt(np.sum((pos[i] - pos[j]) ** 2, axis=1))
        forces = self.spring_constant * (
                distance - self.equilibrium_distance) / distance * (
                         pos[i] - pos[j])
        return np.bincount(fo)
