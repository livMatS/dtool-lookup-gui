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
"""Unit tests for the authentication, config-details and server-versions dialogs.

These Gtk.Window dialogs are self-contained (their __init__ does not touch the
application), so they are constructed directly. The config/versions dialogs
fetch from the lookup server asynchronously; get_config / get_versions are
mocked so no server is contacted.
"""
import asyncio

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dtool_lookup_gui.views.authentication_dialog import AuthenticationDialog
from dtool_lookup_gui.views.config_details import ConfigDialog
from dtool_lookup_gui.views.server_versions_dialog import ServerVersionsDialog


# ===========================================================================
# AuthenticationDialog
# ===========================================================================

def test_authentication_dialog_prefills_credentials():
    dialog = AuthenticationDialog(username="bob", password="secret")
    assert dialog.username_entry.get_text() == "bob"
    assert dialog.password_entry.get_text() == "secret"


def test_authentication_dialog_blank_by_default():
    dialog = AuthenticationDialog()
    assert dialog.username_entry.get_text() == ""
    assert dialog.password_entry.get_text() == ""


def test_authentication_dialog_apply_invokes_callback():
    apply = MagicMock()
    dialog = AuthenticationDialog(apply=apply)
    dialog.username_entry.set_text("alice")
    dialog.password_entry.set_text("pw")
    dialog.on_apply_clicked(None)
    apply.assert_called_once_with("alice", "pw")


def test_authentication_dialog_cancel_does_not_invoke_callback():
    apply = MagicMock()
    dialog = AuthenticationDialog(apply=apply)
    dialog.on_cancel_clicked(None)
    apply.assert_not_called()


# ===========================================================================
# ConfigDialog
# ===========================================================================

def test_config_dialog_formats_server_config_as_json_lines():
    dialog = ConfigDialog()
    lines = dialog._format_server_config({"a": 1, "b": [1, 2]})
    assert lines[0] == "{"
    assert any('"a": 1' in line for line in lines)


def test_config_dialog_delete_hides_window():
    dialog = ConfigDialog()
    assert dialog.on_config_delete(None, None) is True


@pytest.mark.asyncio
async def test_config_dialog_retrieve_populates_buffer():
    dialog = ConfigDialog()
    with patch("dtool_lookup_gui.views.config_details.get_config",
               AsyncMock(return_value={"server": "x"})):
        await dialog._retrieve_config()
    buffer = dialog.config_text_view.get_buffer()
    text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
    assert '"server"' in text


@pytest.mark.asyncio
async def test_config_dialog_show_schedules_retrieve():
    dialog = ConfigDialog()
    with patch("dtool_lookup_gui.views.config_details.get_config",
               AsyncMock(return_value={"k": "v"})) as mock_get_config:
        dialog.on_config_show(None)
        await asyncio.sleep(0.05)  # let the scheduled task run
    mock_get_config.assert_awaited()


# ===========================================================================
# ServerVersionsDialog
# ===========================================================================

def test_server_versions_dialog_formats_sorted_by_key_length():
    dialog = ServerVersionsDialog()
    formatted = dialog._format_server_versions({"dtool": "1.0", "x": "2"})
    # shorter key name first
    assert formatted == "x: <b>2</b>\ndtool: <b>1.0</b>"


def test_server_versions_dialog_delete_hides_window():
    dialog = ServerVersionsDialog()
    assert dialog.on_delete(None, None) is True


@pytest.mark.asyncio
async def test_server_versions_dialog_retrieve_sets_label():
    dialog = ServerVersionsDialog()
    with patch("dtool_lookup_gui.views.server_versions_dialog.get_versions",
               AsyncMock(return_value={"dtool": "1.0"})):
        await dialog._retrieve_versions()
    assert "dtool" in dialog.server_versions_label.get_text()


@pytest.mark.asyncio
async def test_server_versions_dialog_show_schedules_retrieve():
    dialog = ServerVersionsDialog()
    with patch("dtool_lookup_gui.views.server_versions_dialog.get_versions",
               AsyncMock(return_value={"dtool": "1.0"})) as mock_get_versions:
        dialog.on_show(None)
        await asyncio.sleep(0.05)  # let the scheduled task run
    mock_get_versions.assert_awaited()
