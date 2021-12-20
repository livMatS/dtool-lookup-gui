#
# Copyright 2021 Johannes Hörmann
#           2020-2021 Lars Pastewka
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

from math import pi, sqrt
_sqrt3 = sqrt(3)

import numpy as np

from gi.repository import GLib, GObject, Gdk, Gtk

from ..models.simple_graph import GraphLayout
from ..utils.query import dump_single_line_query_text

from .graph_popover import DtoolGraphPopover


logger = logging.getLogger(__name__)

def circle(context, x, y):
    context.arc(x, y, 0.5, 0, 2 * pi)
    context.close_path()


def square(context, x, y):
    context.rectangle(x - 0.4, y - 0.4, 0.8, 0.8)


def triangle(context, x, y):
    height = 0.5*_sqrt3
    context.move_to(x, y - 0.5*height)
    context.line_to(x + 0.5, y + 0.5*height)
    context.line_to(x - 0.5, y + 0.5*height)
    context.close_path()


class DtoolGraphWidget(Gtk.DrawingArea):
    __gtype_name__ = 'DtoolGraphWidget'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer = None
        self._graph = None
        self._layout = None

        self._search_by_uuid = None

        self._popover = DtoolGraphPopover(on_show_clicked=self.on_show_clicked)
        self._popover.set_relative_to(self)

        self.connect('realize', self.on_realize)
        self.connect('draw', self.on_draw)
        self.connect('motion-notify-event', self.on_motion_notify)
        self.set_events(Gdk.EventMask.POINTER_MOTION_MASK)

    @property
    def search_by_uuid(self):
        return self._search_by_uuid

    @search_by_uuid.setter
    def search_by_uuid(self, func):
        self._search_by_uuid = func

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, graph):
        self._graph = graph
        self._graph.set_vertex_properties('state', np.zeros(self._graph.nb_vertices, dtype=bool))
        self._layout = GraphLayout(self._graph)
        if self._timer is None:
            self._timer = GObject.timeout_add(10, self.on_timeout, self)

    def __del__(self):
        if self._timer is not None:
            GObject.source_remove(self._timer)

    def _cairo_scale(self, area, context):
        w, h = area.get_allocated_width(), area.get_allocated_height()
        positions = self._layout.positions
        min_x = np.min(positions[:, 0]) - 1
        max_x = np.max(positions[:, 0]) + 1
        min_y = np.min(positions[:, 1]) - 1
        max_y = np.max(positions[:, 1]) + 1
        s = min(w / (max_x - min_x), h / (max_y - min_y))
        context.scale(s, s)
        context.translate((w / s - min_x - max_x) / 2,
                          (h / s - min_y - max_y) / 2)

    def on_realize(self, area):
        pass

    def on_draw(self, area, context):
        if self._graph is None or self._layout is None:
            return

        context.set_source_rgb(1, 1, 1)
        context.paint()

        # Set scale transformation
        self._cairo_scale(area, context)

        # Get positions from layouter
        positions = self._layout.positions
        kind = self._graph.get_vertex_properties('kind')
        state = self._graph.get_vertex_properties('state')

        # Draw vertices
        root_color = Gdk.color_parse('lightgreen')
        does_not_exist_color = Gdk.color_parse('red')
        dependency_color = Gdk.color_parse('lightblue')
        for i, ((x, y), k, s) in enumerate(zip(positions, kind, state)):
            if k == 'root':
                context.set_source_rgb(*root_color.to_floats())
                square(context, x, y)
            elif k == 'does-not-exist':
                context.set_source_rgb(*does_not_exist_color.to_floats())
                triangle(context, x, y)
            else:
                context.set_source_rgb(*dependency_color.to_floats())
                circle(context, x, y)
            if s:
                context.fill_preserve()
                context.set_source_rgb(0, 0, 0)
                context.set_line_width(0.1)
                context.stroke()
            else:
                context.fill()

        # Draw edges
        context.set_source_rgb(0, 0, 0)
        context.set_line_width(0.1)
        for i, j in self._graph.edges:
            # Start and end position of arrow
            i_pos = positions[i].copy()
            j_pos = positions[j].copy()
            # Adjust to radius of circle
            ij = i_pos - j_pos
            normal = ij / np.linalg.norm(ij)
            perpendicular = np.array([normal[1], -normal[0]])
            i_pos -= 0.5 * normal
            j_pos += 0.5 * normal
            # Draw line
            context.move_to(*(i_pos - 0.05 * normal))
            context.line_to(*(j_pos + 0.1 * normal))
            context.stroke()
            # Draw arrow head
            context.move_to(*i_pos)
            context.line_to(*(i_pos - 0.2 * normal - 0.2 * perpendicular))
            context.line_to(*(i_pos - 0.2 * normal + 0.2 * perpendicular))
            context.fill()
            context.close_path()

    def on_motion_notify(self, area, event):
        context = area.get_window().cairo_create()
        self._cairo_scale(area, context)

        positions = self._layout.positions
        state = np.array(self._graph.get_vertex_properties('state'))
        uuids = np.array(self._graph.get_vertex_properties('uuid'))
        names = np.array(self._graph.get_vertex_properties('name'))

        cursor_pos = np.array(context.device_to_user(event.x, event.y))
        dist_sq = np.sum((positions - cursor_pos) ** 2, axis=1)

        new_state = dist_sq < 0.25
        if np.any(new_state != state):
            state = new_state
            self._graph.set_vertex_properties('state', state)

            self.queue_draw()

            if np.any(state):
                # Show popover
                positions = self._layout.positions
                x, y = positions[state][0]
                rect = Gdk.Rectangle()
                rect.x, rect.y = context.user_to_device(x, y + 0.5)
                self._popover.set_pointing_to(rect)
                self._current_uuid = uuids[state][0]
                self._popover.uuid = self._current_uuid
                self._popover.name = names[state][0]
                self._popover.show()

        if not np.any(state):
            # Hide popover if no node is active
            self._popover.hide()

    def on_show_clicked(self, user_data):
        self._popover.hide()
        # use an action to evoke search. If an according action does not exist, then nothing happens.
        search_text = dump_single_line_query_text({"uuid": self._current_uuid})
        self.get_action_group("win").activate_action('search-select-show', GLib.Variant.new_string(search_text))

    def on_timeout(self, user_data):
        try:
            self._layout.iterate()
        except Exception as e:
            logger.error(str(e))
        self.queue_draw()
        return True


GObject.type_register(DtoolGraphWidget)
