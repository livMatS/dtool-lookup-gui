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
"""Unit tests for utils.logging.

The GTK buffer log handlers are exercised against real Gtk.TextBuffer / Label /
InfoBar widgets (no window required). Covered are the handlers actually wired up
in the app (appending text buffer, single-message info bar) plus the
prepending text-buffer handler, the entry-buffer handlers, the max_lines
validation, and the emit error path.
"""
import logging
from unittest.mock import MagicMock

import pytest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from dtool_lookup_gui.utils import logging as L


def _record(msg, level=logging.INFO):
    return logging.LogRecord("test", level, __file__, 0, msg, None, None)


def _text(buffer):
    return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)


# ===========================================================================
# helpers and filters
# ===========================================================================

def test_log_nested_emits_one_call_per_line():
    lines = []
    L._log_nested(lines.append, {"a": 1, "b": {"c": 2}})
    assert len(lines) > 1
    assert any('"a"' in line for line in lines)


def test_default_filter_blocks_excluded_pattern():
    assert L.DefaultFilter().filter(_record("Unclosed client session")) is False


def test_default_filter_allows_unmatched_message():
    assert L.DefaultFilter().filter(_record("a normal message")) is True


# ===========================================================================
# GtkBufferHandler.max_lines validation
# ===========================================================================

def test_max_lines_none_means_no_limit():
    assert L.GtkBufferHandler(max_lines=None).max_lines is None


def test_max_lines_accepts_non_negative_int():
    assert L.GtkBufferHandler(max_lines=5).max_lines == 5


@pytest.mark.parametrize("bad", [-1, "x", 1.5])
def test_max_lines_rejects_invalid(bad):
    with pytest.raises(ValueError):
        L.GtkBufferHandler(max_lines=bad)


def test_emit_routes_exceptions_to_handle_error():
    handler = L.FormattedAppendingGtkTextBufferHandler(text_buffer=Gtk.TextBuffer())
    handler.handleError = MagicMock()
    handler._insert_into_buffer = MagicMock(side_effect=RuntimeError("boom"))
    handler.emit(_record("x"))
    handler.handleError.assert_called_once()


# ===========================================================================
# Appending text-buffer handler (used by the log window)
# ===========================================================================

def test_appending_text_buffer_writes_message():
    buf = Gtk.TextBuffer()
    handler = L.FormattedAppendingGtkTextBufferHandler(text_buffer=buf)
    handler.emit(_record("hello append"))
    assert "hello append" in _text(buf)


def test_appending_text_buffer_crops_to_max_lines():
    buf = Gtk.TextBuffer()
    handler = L.FormattedAppendingGtkTextBufferHandler(text_buffer=buf, max_lines=3)
    for i in range(10):
        handler.emit(_record(f"line{i}"))
    # newest message survives, line count stays bounded
    assert "line9" in _text(buf)
    assert buf.get_line_count() <= 4


# ===========================================================================
# Prepending text-buffer handler
# ===========================================================================

def test_prepending_text_buffer_inserts_newest_first():
    buf = Gtk.TextBuffer()
    handler = L.FormattedPrependingGtkTextBufferHandler(text_buffer=buf)
    handler.emit(_record("first"))
    handler.emit(_record("second"))
    text = _text(buf)
    assert text.index("second") < text.index("first")


def test_prepending_text_buffer_crops_to_max_lines():
    buf = Gtk.TextBuffer()
    handler = L.FormattedPrependingGtkTextBufferHandler(text_buffer=buf, max_lines=2)
    for i in range(6):
        handler.emit(_record(f"p{i}"))
    assert buf.get_line_count() <= 3


# ===========================================================================
# Label / InfoBar handlers (info bar used by the main window)
# ===========================================================================

def test_label_handler_keeps_last_lines_when_too_long():
    label = Gtk.Label()
    handler = L.FormattedSingleMessageGtkLabelHandler(label=label, max_lines=1)
    handler.emit(_record("a\nb\nc"))
    assert label.get_text().strip().endswith("c")


def test_infobar_handler_sets_label_and_reveals():
    label = Gtk.Label()
    info_bar = Gtk.InfoBar()
    handler = L.FormattedSingleMessageGtkInfoBarHandler(label=label, info_bar=info_bar)
    handler.emit(_record("important"))
    assert "important" in label.get_text()
    assert info_bar.get_revealed() is True


# ===========================================================================
# Entry-buffer handlers
# ===========================================================================

def test_entry_buffer_handler_construction_uses_default_max_lines():
    handler = L.AppendingGtkEntryBufferHandler(entry_buffer=Gtk.EntryBuffer())
    assert handler.max_lines == L.DEFAULT_ENTRY_MAX_LINES


def test_appending_entry_buffer_keeps_latest_message():
    buf = Gtk.EntryBuffer()
    handler = L.AppendingGtkEntryBufferHandler(entry_buffer=buf, max_lines=3)
    for i in range(5):
        handler.emit(_record(f"entry{i}"))
    text = buf.get_text()
    assert "entry4" in text
    assert len(text.splitlines()) <= 3


def test_appending_entry_buffer_shortens_multiline_message():
    buf = Gtk.EntryBuffer()
    handler = L.AppendingGtkEntryBufferHandler(entry_buffer=buf, max_lines=2)
    handler.emit(_record("a\nb\nc\nd\ne"))
    assert "..." in buf.get_text()


def test_single_message_entry_buffer_stores_only_last_message():
    buf = Gtk.EntryBuffer()
    handler = L.SingleMessageGtkEntryBufferHandler(entry_buffer=buf, max_lines=5)
    handler.emit(_record("first"))
    handler.emit(_record("second"))
    assert buf.get_text() == "second"


def test_single_message_entry_buffer_shortens_multiline_message():
    buf = Gtk.EntryBuffer()
    handler = L.SingleMessageGtkEntryBufferHandler(entry_buffer=buf, max_lines=2)
    handler.emit(_record("a\nb\nc\nd\ne"))
    # The middle is elided with an ellipsis marker.
    assert "..." in buf.get_text()
