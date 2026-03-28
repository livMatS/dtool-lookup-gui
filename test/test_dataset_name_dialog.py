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
"""Tests for DatasetNameDialog validation — fixes #199.

The dialog must show an inline error and NOT call on_confirmation when
the name is empty or contains invalid characters, and must call
on_confirmation and close when the name is valid.
"""
import pytest
from unittest.mock import MagicMock

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from dtool_lookup_gui.views.dataset_name_dialog import DatasetNameDialog


@pytest.fixture
def confirmation_callback():
    return MagicMock()


@pytest.fixture
def dialog(confirmation_callback):
    dlg = DatasetNameDialog(on_confirmation=confirmation_callback)
    yield dlg
    # Destroy if not already destroyed by on_apply_clicked
    try:
        dlg.destroy()
    except Exception:
        pass


def test_valid_name_calls_confirmation(dialog, confirmation_callback):
    """A valid dataset name must call on_confirmation and close the dialog."""
    dialog.name_entry.set_text("my-valid-dataset-name")
    dialog.on_apply_clicked(None)
    confirmation_callback.assert_called_once_with("my-valid-dataset-name")


def test_valid_name_with_whitespace_stripped(confirmation_callback):
    """Leading/trailing whitespace is stripped before validation and confirmation."""
    dlg = DatasetNameDialog(on_confirmation=confirmation_callback)
    dlg.name_entry.set_text("  valid-name  ")
    dlg.on_apply_clicked(None)
    confirmation_callback.assert_called_once_with("valid-name")


def test_empty_name_shows_error(dialog, confirmation_callback):
    """Empty name must show an error and NOT call on_confirmation."""
    dialog.name_entry.set_text("")
    dialog.on_apply_clicked(None)

    confirmation_callback.assert_not_called()
    assert dialog.error_label.get_visible(), "Error label must be visible for empty name"
    assert dialog.error_label.get_text() != ""


def test_invalid_chars_shows_error(dialog, confirmation_callback):
    """Name with invalid characters must show an error and NOT call on_confirmation."""
    dialog.name_entry.set_text("invalid name with spaces!")
    dialog.on_apply_clicked(None)

    confirmation_callback.assert_not_called()
    assert dialog.error_label.get_visible(), "Error label must be visible for invalid name"
    error_text = dialog.error_label.get_text()
    assert "invalid" in error_text.lower() or "allowed" in error_text.lower(), \
        f"Error message should explain the invalid characters, got: {error_text!r}"


def test_invalid_chars_slash(dialog, confirmation_callback):
    """Names with slashes are invalid (would create subdirectories)."""
    dialog.name_entry.set_text("invalid/name")
    dialog.on_apply_clicked(None)
    confirmation_callback.assert_not_called()
    assert dialog.error_label.get_visible()


def test_error_clears_on_changed(dialog, confirmation_callback):
    """Typing in the entry must clear the error state."""
    # Trigger an error first
    dialog.name_entry.set_text("")
    dialog.on_apply_clicked(None)
    assert dialog.error_label.get_visible()

    # Simulate user typing
    dialog.name_entry.set_text("f")
    # error_label should be hidden now (changed signal fired)
    assert not dialog.error_label.get_visible(), \
        "Error label must be hidden when user starts typing"


def test_valid_name_dots_and_underscores(confirmation_callback):
    """Names with dots, underscores and hyphens are valid."""
    dlg = DatasetNameDialog(on_confirmation=confirmation_callback)
    dlg.name_entry.set_text("my_dataset-v1.0")
    dlg.on_apply_clicked(None)
    confirmation_callback.assert_called_once_with("my_dataset-v1.0")


def test_whitespace_only_shows_error(dialog, confirmation_callback):
    """Whitespace-only name (strips to empty) must show error."""
    dialog.name_entry.set_text("   ")
    dialog.on_apply_clicked(None)
    confirmation_callback.assert_not_called()
    assert dialog.error_label.get_visible()
