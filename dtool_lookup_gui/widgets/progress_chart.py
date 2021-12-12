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

import logging

from math import pi, sqrt

import numpy as np

from gi.repository import GLib, GObject, Gdk, Gtk

from ..models.simple_graph import GraphLayout
from ..utils.query import dump_single_line_query_text

from .graph_popover import DtoolGraphPopover


class DtoolProgressChart(Gtk.DrawingArea):
    __gtype_name__ = 'DtoolProgressChart'

    _background_color = Gdk.color_parse('lightgray')
    _pie_color = Gdk.color_parse('gray')

    def __init__(self, *args, **kwargs):
        self._fraction = kwargs.pop('fraction', 0)
        super().__init__(*args, **kwargs)
        self.connect('draw', self.on_draw)

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, value):
        if value < 0 or value > 1:
            raise ValueError('Progress fraction must be between 0 and 1.')
        self._fraction = value

    def _cairo_scale(self, area, context):
        w, h = area.get_allocated_width(), area.get_allocated_height()
        print(w, h)
        s = min(w, h)
        context.translate(w / 2, h / 2)
        context.scale(s, s)

    def on_draw(self, area, context):
        # context.set_source_rgb(1, 1, 1)
        # context.paint()

        # Set scale transformation
        self._cairo_scale(area, context)

        # Draw background circle
        context.set_source_rgb(*self._background_color.to_floats())
        context.arc(0, 0, 0.5, 0, 2 * pi)
        context.close_path()
        context.fill()

        # Draw pie
        context.set_source_rgb(*self._pie_color.to_floats())
        context.arc(0, 0, 0.5, 3* pi / 2, 3 * pi /2 + 2 * pi * self._fraction)
        context.line_to(0, 0)
        context.close_path()
        context.fill()

        # Draw fraction
        # context.set_source_rgb(0, 0, 0)
        # context.set_line_width(0.1)


GObject.type_register(DtoolProgressChart)
