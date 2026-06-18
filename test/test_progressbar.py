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
"""Unit tests for the ProgressBar context manager (utils.progressbar).

ProgressBar mimics click.progressbar: with no widget it only logs; with a
widget it drives set_fraction/set_step/set_text. The widget is a mock, so no
GTK widget tree is needed.
"""
from unittest.mock import MagicMock

from dtool_lookup_gui.utils.progressbar import ProgressBar


# --- no-widget (logging-only) behaviour ------------------------------------

def test_context_manager_without_widget_runs():
    with ProgressBar(length=10, label="Copying") as bar:
        assert bar is not None
        bar.update(5)  # must not raise without a widget


def test_label_property_round_trip():
    bar = ProgressBar(length=10)
    bar.label = "new label"
    assert bar.label == "new label"


def test_item_show_func_property_round_trip():
    bar = ProgressBar(length=10, label="x")

    def show(step):
        return f"item{step}"

    bar.item_show_func = show
    assert bar.item_show_func is show


# --- with a widget ---------------------------------------------------------

def test_enter_initializes_widget_fraction():
    widget = MagicMock()
    with ProgressBar(length=10, label="Copying", pb=widget):
        pass
    widget.set_fraction.assert_any_call(0.0)
    widget.set_step.assert_any_call(0, 10)


def test_update_advances_widget_fraction_and_step():
    widget = MagicMock()
    with ProgressBar(length=10, label="Copying", pb=widget) as bar:
        bar.update(5)
    widget.set_fraction.assert_any_call(0.5)
    widget.set_step.assert_any_call(5, 10)


def test_update_accumulates_steps():
    widget = MagicMock()
    bar = ProgressBar(length=4, pb=widget)
    bar.update(1)
    bar.update(1)
    widget.set_fraction.assert_called_with(0.5)  # 2/4


def test_set_text_uses_label_on_widget():
    widget = MagicMock()
    bar = ProgressBar(length=10, label="Copying", pb=widget)
    bar.label = "Downloading"
    widget.set_text.assert_called_with("Downloading")


def test_set_text_with_item_show_func_on_widget():
    widget = MagicMock()
    bar = ProgressBar(length=10, label="Copying", pb=widget)
    bar.item_show_func = lambda step: f"file{step}"
    widget.set_text.assert_called()


def test_without_label_hides_widget_text():
    widget = MagicMock()
    with ProgressBar(length=10, pb=widget):
        pass
    widget.set_show_text.assert_called_with(False)
