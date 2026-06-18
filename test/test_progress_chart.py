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
"""Unit tests for the DtoolProgressChart drawing-area widget.

The widget draws a pie chart with cairo; on_draw is exercised against a real
cairo context backed by an in-memory image surface, so no realized window is
needed.
"""
import cairo

from dtool_lookup_gui.widgets.progress_chart import DtoolProgressChart


def test_fraction_initialised_from_kwarg():
    assert DtoolProgressChart(fraction=0.25).fraction == 0.25


def test_fraction_defaults_to_zero():
    assert DtoolProgressChart().fraction == 0


def test_set_fraction_updates_value():
    chart = DtoolProgressChart()
    chart.set_fraction(0.75)
    assert chart.fraction == 0.75


def test_set_text_does_not_raise():
    # set_text only logs (the chart has no text), but must remain callable.
    DtoolProgressChart().set_text("50%")


def test_on_draw_renders_without_error():
    chart = DtoolProgressChart(fraction=0.5)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
    context = cairo.Context(surface)
    # Should execute the full cairo drawing path (scale, background, pie).
    chart.on_draw(chart, context)


def test_on_draw_handles_zero_and_full_fraction():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
    for fraction in (0.0, 1.0):
        chart = DtoolProgressChart(fraction=fraction)
        chart.on_draw(chart, cairo.Context(surface))
