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

from math import pi

import numpy as np

from gi.repository import Gdk, Gtk


def circle(context, x, y):
    context.arc(x, y, 0.5, 0, 2 * pi)
    context.close_path()


def square(context, x, y):
    context.rectangle(x - 0.4, y - 0.4, 0.8, 0.8)


class GraphWidget(Gtk.DrawingArea):
    def __init__(self, builder, graph, pos, uuids, names):
        super().__init__()
        self.graph = graph
        self.pos = np.array(pos)
        self.uuids = np.array(uuids)
        self.names = np.array(names)
        self.state = np.zeros(len(self.pos), dtype=bool)

        # Popover widget
        self.popover = builder.get_object('dependency-popover')
        self.popover.set_relative_to(self)
        self.uuid_label = builder.get_object('dependency-uuid')
        self.name_label = builder.get_object('dependency-name')
        self.search_entry = builder.get_object('search-entry')

        self._current_uuid = None

        # Event signals
        self.connect('motion-notify-event', self.on_motion_notify)

        self.set_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.connect('realize', self.on_realize)
        self.connect('draw', self.on_draw)

        builder.get_object('dependency-show-dataset-button').connect(
            'clicked', self.on_show_clicked)

    def _cairo_scale(self, area, context):
        w, h = area.get_allocated_width(), area.get_allocated_height()
        min_x = np.min(self.pos[:, 0]) - 1
        max_x = np.max(self.pos[:, 0]) + 1
        min_y = np.min(self.pos[:, 1]) - 1
        max_y = np.max(self.pos[:, 1]) + 1
        s = min(w / (max_x - min_x), h / (max_y - min_y))
        context.scale(s, s)
        context.translate((w / s - min_x - max_x) / 2,
                          (h / s - min_y - max_y) / 2)

    def on_realize(self, area):
        pass

    def on_draw(self, area, context):
        context.set_source_rgb(1, 1, 1)
        context.paint()

        # Set scale transformation
        self._cairo_scale(area, context)

        # Draw vertices
        for i, ((x, y), s) in enumerate(zip(self.pos, self.state)):
            context.set_source_rgb(0.5, 0.5, 0.7)
            if i == 0:
                square(context, x, y)
            else:
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
        for i, j in self.graph.edges():
            # Start and end position of arrow
            i_pos = self.pos[int(i)].copy()
            j_pos = self.pos[int(j)].copy()
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
            context.move_to(*j_pos)
            context.line_to(*(j_pos + 0.2 * normal + 0.2 * perpendicular))
            context.line_to(*(j_pos + 0.2 * normal - 0.2 * perpendicular))
            context.close_path()
            context.fill()

    def on_motion_notify(self, area, event):
        context = area.get_window().cairo_create()
        self._cairo_scale(area, context)
        cursor_pos = np.array(context.device_to_user(event.x, event.y))
        dist_sq = np.sum((self.pos - cursor_pos) ** 2, axis=1)

        new_state = dist_sq < 0.25
        if np.any(new_state != self.state):
            self.state = new_state
            self.queue_draw()

            if np.any(self.state):
                # Show popover
                x, y = self.pos[self.state][0]
                rect = Gdk.Rectangle()
                rect.x, rect.y = context.user_to_device(x, y + 0.5)
                self.popover.set_pointing_to(rect)
                self._current_uuid = self.uuids[self.state][0]
                self.uuid_label.set_text(self._current_uuid)
                self.name_label.set_text(self.names[self.state][0])
                self.popover.show()

        if not np.any(self.state):
            # Hide popover if no node is active
            self.popover.hide()

    def on_show_clicked(self, user_data):
        self.popover.hide()
        self.search_entry.set_text(f'uuid:{self._current_uuid}')
