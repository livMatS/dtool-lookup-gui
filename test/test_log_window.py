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
"""Unit tests for views.log_window.

The LogWindow the main window builds during activation is reached via the
running_app fixture and its non-modal signal/action handlers are exercised
directly. The modal save handler (Gtk.FileChooserDialog.run) needs user
interaction and is out of scope.
"""
import logging

import pytest

from gi.repository import GLib

from dtool_lookup_gui.views.main_window import MainWindow


def _log_window(app):
    main_window = [w for w in app.get_windows() if isinstance(w, MainWindow)][0]
    return main_window.log_window


def _buffer_text(buf):
    return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)


@pytest.mark.asyncio
async def test_do_loglevel_changed_updates_combo_box(running_app):
    log_window = _log_window(running_app)
    model = log_window.loglevel_combo_box.get_model()
    current = model[log_window.loglevel_combo_box.get_active_iter()][0]
    target = logging.DEBUG if current != logging.DEBUG else logging.INFO

    log_window.do_loglevel_changed(None, GLib.Variant.new_uint16(target))

    active = model[log_window.loglevel_combo_box.get_active_iter()][0]
    assert active == target


@pytest.mark.asyncio
async def test_on_show_does_not_raise(running_app):
    log_window = _log_window(running_app)
    log_window.on_show(None)


@pytest.mark.asyncio
async def test_on_delete_hides_instead_of_destroying(running_app):
    log_window = _log_window(running_app)
    assert log_window.on_delete(None, None) is True


@pytest.mark.asyncio
async def test_on_log_switch_state_set_does_not_raise(running_app):
    log_window = _log_window(running_app)
    log_window.on_log_switch_state_set(log_window.log_switch, True)


@pytest.mark.asyncio
async def test_on_clear_clicked_empties_buffer(running_app):
    log_window = _log_window(running_app)
    log_window.log_buffer.set_text("some log content")
    log_window.on_clear_clicked(None)
    assert _buffer_text(log_window.log_buffer) == ""


@pytest.mark.asyncio
async def test_on_copy_clicked_does_not_raise(running_app):
    log_window = _log_window(running_app)
    log_window.log_buffer.set_text("copy me")
    log_window.on_copy_clicked(None)


@pytest.mark.asyncio
async def test_on_destroy_removes_log_handler(running_app):
    log_window = _log_window(running_app)
    root_logger = logging.getLogger()
    assert log_window.log_handler in root_logger.handlers
    log_window.on_destroy(None)
    assert log_window.log_handler not in root_logger.handlers
