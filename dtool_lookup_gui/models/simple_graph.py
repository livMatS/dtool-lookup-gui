#
# Copyright 2020-2021 Lars Pastewka
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

import logging

import numpy as np
from scipy.special import erf

logger = logging.getLogger(__name__)


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
    """
    Simple graph layouter that uses spring and electrostatic forces between
    vertices and the Fast Intertial Relaxation Engine (FIRE) for optimization.
    """

    def __init__(self, graph, spring_constant=10, equilibrium_distance=2,
                 coulomb=1, core_length=2, coulomb_exponent=1, mass=1,
                 max_timestep=1, minsteps=10, inc_timestep=1.2,
                 dec_timestep=0.5, mix=0.1, dec_mix=0.99,
                 init_iter=100):
        self.graph = graph
        self.spring_constant = spring_constant
        self.equilibrium_distance = equilibrium_distance
        self.coulomb = coulomb
        self.core_length = core_length
        self.coulomb_exponent = coulomb_exponent
        self.mass = mass
        self.max_timestep = max_timestep
        self.minsteps = minsteps
        self.inc_timestep = inc_timestep
        self.dec_timestep = dec_timestep
        self.initial_mix = mix
        self.dec_mix = dec_mix
        self.init_iter = init_iter

        self.timestep = max_timestep
        self.mix = mix
        self.cut = minsteps

        self._energy = None

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
        for i in range(self.init_iter):
            self.iterate()

    def _compute_spring_energy_and_forces(self, pos):
        nb_vertices = self.graph.nb_vertices
        if nb_vertices <= 1:
            return 0, np.zeros_like(pos)

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
        if nb_vertices <= 1:
            return 0, np.zeros_like(pos)

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
        drnorm_n = abs_dr_n / self.core_length
        e_n = self.coulomb * erf(drnorm_n ** self.coulomb_exponent) / \
              (abs_dr_n ** self.coulomb_exponent)

        # Forces (per pair)
        de_n = self.coulomb * self.coulomb_exponent * (
                -erf(drnorm_n ** self.coulomb_exponent)
                + 2 * np.exp(-drnorm_n ** (2 * self.coulomb_exponent))
                * drnorm_n ** self.coulomb_exponent / np.sqrt(np.pi)) / \
               abs_dr_n ** (self.coulomb_exponent + 1)

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

        old_energy = self._energy
        old_positions = self._positions.copy()
        old_velocities = self._velocities.copy()

        it = 0

        action = 'uphill e'
        while action == 'uphill e' and it < 5:
            # Verlet step 1
            self._velocities += 0.5 * self._forces * self.timestep / self.mass
            self._positions += self._velocities * self.timestep

            # Recompute forces
            self._energy, self._forces = self._compute_spring_energy_and_forces(
                self._positions)
            e, f = self._compute_coulomb_energy_and_forces(self._positions)
            self._energy += e
            self._forces += f

            # Verlet step 2
            self._velocities += 0.5 * self._forces * self.timestep / self.mass

            if self._energy is not None and old_energy is not None and \
                    self._energy > old_energy:
                # The energy did not decrease, decrease time step and retry!
                self._positions = old_positions.copy()
                self._velocities = old_velocities.copy()
                self.timestep *= self.dec_timestep

                action = 'uphill e'
            else:
                # Adjust velocities according to the FIRE algorithm
                v_dot_f = np.sum(self._velocities * self._forces)
                if v_dot_f < 0:
                    self._velocities = np.zeros_like(self._velocities)
                    self.cut = self.minsteps
                    self.timestep = self.timestep * self.dec_timestep
                    self.mix = self.initial_mix

                    action = 'uphill v*f'
                else:
                    v_dot_v = np.sum(self._velocities ** 2)
                    f_dot_f = np.sum(self._forces ** 2)

                    help = 0.0
                    if f_dot_f > 0:
                        help = self.mix * np.sqrt(v_dot_v / f_dot_f)

                    self._velocities = (1 - self.mix) * self._velocities + \
                                       help * self._forces

                    if self.cut < 0:
                        self.timestep = min(self.timestep * self.inc_timestep,
                                            self.max_timestep)
                        self.mix = self.mix * self.dec_mix
                    else:
                        self.cut -= 1

                    action = 'mix'

            it += 1
            logger.debug(f'FIRE: {action}, '
                         f'energy: {self._energy}, '
                         f'(old energy: {old_energy}, '
                         f'max |force|: {np.sqrt(np.max(np.sum(self._forces ** 2, axis=1)))},'
                         f' timestep: {self.timestep}')
