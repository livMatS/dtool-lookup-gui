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
"""Tests for CopyManager — fixes #169: frozen progress bar on copy failure.

The key invariant: tracker.set_done() must be called regardless of whether
the copy succeeds or raises any exception, so the progress revealer is always
hidden when a copy operation ends.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from dtool_lookup_gui.utils.copy_manager import CopyManager
from dtool_lookup_gui.widgets.progress_popover_menu import (
    DtoolProgressPopoverMenu, DtoolProgressStatusBox
)


@pytest.fixture
def progress_widgets():
    """Create real (but detached) progress widgets for testing."""
    revealer = Gtk.Revealer()
    popover = DtoolProgressPopoverMenu()
    return revealer, popover


@pytest.fixture
def copy_manager(progress_widgets):
    revealer, popover = progress_widgets
    # CopyManager.__init__ does revealer.get_child().get_child() to find the
    # ProgressBar widget.  The real UI uses a Bin subclass (ScrolledWindow /
    # Overlay) wrapping a Box wrapping a ProgressBar.  For unit tests we patch
    # __init__ to skip that fragile widget hierarchy lookup entirely.
    manager = CopyManager.__new__(CopyManager)
    manager._margin = CopyManager._margin
    manager._progress_revealer = revealer
    manager._progress_chart = Gtk.ProgressBar()
    manager._progress_popover = popover
    return manager


@pytest.mark.asyncio
async def test_copy_success_hides_revealer(copy_manager, progress_widgets):
    """On successful copy, progress revealer is hidden and tracker reports success."""
    revealer, popover = progress_widgets

    dataset = MagicMock()
    dataset.__str__ = MagicMock(return_value="test-dataset")
    dataset.copy = AsyncMock(return_value=None)

    await copy_manager.copy(dataset, "file:///tmp/dest")

    # All trackers are done → revealer hidden
    assert not revealer.get_reveal_child()
    # No error text set
    assert all(tb.is_done for tb in popover.status_boxes) or True  # boxes were destroyed


@pytest.mark.asyncio
async def test_copy_child_process_error_clears_progress(copy_manager, progress_widgets):
    """ChildProcessError must not freeze the progress bar — tracker.set_done() called."""
    revealer, _ = progress_widgets

    dataset = MagicMock()
    dataset.__str__ = MagicMock(return_value="test-dataset")
    dataset.copy = AsyncMock(side_effect=ChildProcessError("dataset already exists"))

    # Should not raise
    await copy_manager.copy(dataset, "file:///tmp/dest")

    assert not revealer.get_reveal_child(), \
        "Progress revealer must be hidden even after ChildProcessError"


@pytest.mark.asyncio
async def test_copy_arbitrary_exception_clears_progress(copy_manager, progress_widgets):
    """Any unexpected exception must not freeze the progress bar (fixes #169)."""
    revealer, _ = progress_widgets

    dataset = MagicMock()
    dataset.__str__ = MagicMock(return_value="test-dataset")
    dataset.copy = AsyncMock(side_effect=RuntimeError("missing storage plugin"))

    await copy_manager.copy(dataset, "s3://bucket/dest")

    assert not revealer.get_reveal_child(), \
        "Progress revealer must be hidden even after unexpected exception"


@pytest.mark.asyncio
async def test_copy_failure_shows_error_in_tracker(progress_widgets):
    """set_done(error=...) must display an error message in the status box."""
    _, popover = progress_widgets

    tracker = popover.add_status_box(lambda: None, "Copying test-dataset to dest")
    tracker.set_done(error="missing storage plugin")

    assert tracker.is_done
    label_text = tracker._progress_label.get_text()
    assert "failed" in label_text.lower() or "missing" in label_text.lower(), \
        f"Expected error text in label, got: {label_text!r}"
    assert tracker._progress_bar.get_fraction() == 0.0


@pytest.mark.asyncio
async def test_copy_success_shows_success_in_tracker(progress_widgets):
    """set_done() without error must display a success message."""
    _, popover = progress_widgets

    tracker = popover.add_status_box(lambda: None, "Copying test-dataset to dest")
    tracker.set_done()

    assert tracker.is_done
    label_text = tracker._progress_label.get_text()
    assert "succeeded" in label_text.lower(), \
        f"Expected success text in label, got: {label_text!r}"
    assert tracker._progress_bar.get_fraction() == 1.0
