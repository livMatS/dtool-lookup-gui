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
from scipy.special import erf


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
    def __init__(self, graph, spring_constant=1, equilibrium_distance=2,
                 coulomb=1, attenuation=0.5, damping_constant=1, timestep=0.5,
                 mass=1):
        self.graph = graph
        self.spring_constant = spring_constant
        self.equilibrium_distance = equilibrium_distance
        self.coulomb = coulomb
        self.attenuation = attenuation
        self.damping_constant = damping_constant
        self.timestep = timestep
        self.mass = mass

        self._initialize_positions()

    @property
    def positions(self):
        return self._positions

    def _initialize_positions(self):
        nb_vertices = self.graph.nb_vertices
        n = int(np.sqrt(nb_vertices)) + 1
        grid = (np.mgrid[:n, :n].T).reshape(-1, 2)[:nb_vertices]
        self._positions = grid.astype(float) * self.equilibrium_distance
        self._velocities = np.zeros_like(self._positions)
        self._forces = np.zeros_like(self._positions)

    def _compute_spring_energy_and_forces(self, pos):
        nb_vertices = self.graph.nb_vertices

        # Neighbor list (edge list)
        i_n = np.array(self.graph.vertex1)
        j_n = np.array(self.graph.vertex2)

        # Vertex distances
        dr_nc = pos[i_n] - pos[j_n]
        abs_dr_n = np.sqrt(np.sum(dr_nc ** 2, axis=1))

        # Energies (per pair)
        e_n = 0.5 * self.spring_constant * (
                abs_dr_n - self.equilibrium_distance) ** 2

        # Forces (per pair)
        de_n = self.spring_constant * (abs_dr_n - self.equilibrium_distance)
        df_nc = 0.5 * de_n.reshape(-1, 1) * dr_nc / abs_dr_n.reshape(-1, 1)

        # Sum for each vertex
        fx_i = np.bincount(j_n, weights=df_nc[:, 0], minlength=nb_vertices) - \
               np.bincount(i_n, weights=df_nc[:, 0], minlength=nb_vertices)
        fy_i = np.bincount(j_n, weights=df_nc[:, 1], minlength=nb_vertices) - \
               np.bincount(i_n, weights=df_nc[:, 1], minlength=nb_vertices)

        # Return energy and forces
        return np.sum(e_n), np.transpose([fx_i, fy_i])

    def _compute_coulomb_energy_and_forces(self, pos):
        nb_vertices = self.graph.nb_vertices

        # Neighbor list (between all atoms)
        i_n, j_n = np.mgrid[:nb_vertices, :nb_vertices]
        i_n.shape = (-1,)
        j_n.shape = (-1,)
        m = i_n != j_n
        i_n = i_n[m]
        j_n = j_n[m]

        # Vertex distances
        dr_nc = pos[i_n] - pos[j_n]
        abs_dr_n = np.sqrt(np.sum(dr_nc ** 2, axis=1))

        # Energies (per pair)
        e_n = self.coulomb * erf(self.attenuation * abs_dr_n) / abs_dr_n

        # Forces (per pair)
        de_n = self.coulomb * (
                -erf(self.attenuation * abs_dr_n) / abs_dr_n ** 2
                + 2 * self.attenuation * np.exp(-(self.attenuation * abs_dr_n) ** 2) / np.sqrt(np.pi))
        df_nc = 0.5 * de_n.reshape(-1, 1) * dr_nc / abs_dr_n.reshape(-1, 1)

        # Sum for each vertex
        fx_i = np.bincount(j_n, weights=df_nc[:, 0], minlength=nb_vertices) - \
               np.bincount(i_n, weights=df_nc[:, 0], minlength=nb_vertices)
        fy_i = np.bincount(j_n, weights=df_nc[:, 1], minlength=nb_vertices) - \
               np.bincount(i_n, weights=df_nc[:, 1], minlength=nb_vertices)

        # Return energy and forces
        return np.sum(e_n), np.transpose([fx_i, fy_i])

    def iterate(self):
        """Carry out a single step of the graph layout optimization"""

        # Verlet step 1
        self._velocities += 0.5 * self._forces * self.timestep / self.mass
        self._positions += self._velocities * self.timestep

        # Recompute forces
        self._energy, self._forces = self._compute_spring_energy_and_forces(
            self._positions)
        e, f = self._compute_coulomb_energy_and_forces(self._positions)
        self._energy += e
        self._forces += f

        # Add damping force
        self._forces += -self.damping_constant * self._velocities

        # Verlet step 2
        self._velocities += 0.5 * self._forces * self.timestep / self.mass
