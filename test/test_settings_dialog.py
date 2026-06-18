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
"""Unit tests for views.settings_dialog.

The pure _get_base_uri helper is tested directly. The signal handlers are
exercised against the real SettingsDialog the main window builds during app
activation (reached via the running_app fixture). The dtool lookup-server
Config global is patched where a handler writes to it, so no config file or
server is touched. The modal file-chooser handlers (import/export/renew) need
user interaction and are out of scope here.
"""
from unittest.mock import MagicMock, patch

import pytest

import dtoolcore

from dtool_lookup_gui.views.main_window import MainWindow
from dtool_lookup_gui.views.settings_dialog import _get_base_uri
from dtool_lookup_gui.models.settings import settings

_CONFIG = "dtool_lookup_gui.views.settings_dialog.Config"


def _settings_dialog(app):
    main_window = [w for w in app.get_windows() if isinstance(w, MainWindow)][0]
    return main_window.settings_dialog


# ===========================================================================
# _get_base_uri (pure)
# ===========================================================================

def test_get_base_uri_s3():
    assert _get_base_uri("DTOOL_S3_ENDPOINT_mybucket") == "s3://mybucket"


def test_get_base_uri_smb():
    assert _get_base_uri("DTOOL_SMB_SERVER_NAME_myserver") == "smb://myserver"


def test_get_base_uri_unknown_key_returns_none():
    assert _get_base_uri("DTOOL_SOMETHING_ELSE") is None


# ===========================================================================
# SettingsDialog signal handlers
# ===========================================================================

@pytest.mark.asyncio
async def test_yaml_linting_switch_updates_settings(running_app):
    dialog = _settings_dialog(running_app)
    dialog.on_yaml_linting_switch_state_set(dialog.yaml_linting_switch, True)
    assert settings.yaml_linting_enabled is True
    dialog.on_yaml_linting_switch_state_set(dialog.yaml_linting_switch, False)
    assert settings.yaml_linting_enabled is False


@pytest.mark.asyncio
async def test_verify_ssl_switch_writes_config(running_app):
    dialog = _settings_dialog(running_app)
    with patch(_CONFIG) as mock_config:
        dialog.on_verify_ssl_certificate_switch_state_set(None, False)
        assert mock_config.verify_ssl is False


@pytest.mark.asyncio
async def test_disable_authentication_switch_toggles_sensitivity(running_app):
    dialog = _settings_dialog(running_app)
    with patch(_CONFIG) as mock_config:
        dialog.on_disable_authentication_switch_state_set(None, True)
        assert mock_config.disable_authentication is True
        # Authentication-related widgets are disabled when auth is off.
        assert dialog.authenticator_url_entry.get_sensitive() is False
        assert dialog.renew_token_button.get_sensitive() is False
        assert dialog.token_entry.get_sensitive() is False

        dialog.on_disable_authentication_switch_state_set(None, False)
        assert dialog.authenticator_url_entry.get_sensitive() is True
        assert dialog.token_entry.get_sensitive() is True


@pytest.mark.asyncio
async def test_on_dtool_config_changed_refreshes(running_app):
    dialog = _settings_dialog(running_app)
    with patch.object(dialog, "_refresh_settings_dialog") as mock_refresh:
        dialog.on_dtool_config_changed(None)
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_item_download_directory_file_set_updates_settings(running_app, tmp_path):
    dialog = _settings_dialog(running_app)
    widget = MagicMock()
    widget.get_file.return_value.get_path.return_value = str(tmp_path)
    dialog.on_item_download_directory_file_chooser_button_file_set(widget)
    assert settings.item_download_directory == str(tmp_path)


@pytest.mark.asyncio
async def test_item_download_directory_file_set_ignores_none(running_app):
    dialog = _settings_dialog(running_app)
    before = settings.item_download_directory
    widget = MagicMock()
    widget.get_file.return_value.get_path.return_value = None
    dialog.on_item_download_directory_file_chooser_button_file_set(widget)
    assert settings.item_download_directory == before


@pytest.mark.asyncio
async def test_on_delete_writes_back_config(running_app):
    dialog = _settings_dialog(running_app)
    dialog.lookup_url_entry.set_text("https://lookup.example.com")
    dialog.dtool_user_full_name_entry.set_text("Jane Doe")
    dialog.dtool_user_email_entry.set_text("jane@example.com")

    with patch(_CONFIG) as mock_config:
        dialog.on_delete(None, None)
        assert mock_config.lookup_url == "https://lookup.example.com"

    # Basic dtool config is written through dtoolcore to the isolated config file.
    assert dtoolcore.utils.get_config_value("DTOOL_USER_FULL_NAME") == "Jane Doe"
    assert dtoolcore.utils.get_config_value("DTOOL_USER_EMAIL") == "jane@example.com"


@pytest.mark.asyncio
async def test_refresh_handles_unset_config(running_app):
    dialog = _settings_dialog(running_app)
    with patch(_CONFIG) as mock_config:
        mock_config.lookup_url = None
        mock_config.token = None
        mock_config.auth_url = None
        mock_config.verify_ssl = None
        mock_config.disable_authentication = None
        dialog._refresh_settings_dialog()

    # Unset lookup config clears the corresponding entries.
    assert dialog.lookup_url_entry.get_text() == ""
    assert dialog.token_entry.get_text() == ""
    assert dialog.authenticator_url_entry.get_text() == ""


@pytest.mark.asyncio
async def test_refresh_populates_entries_from_config(running_app, tmp_path):
    dialog = _settings_dialog(running_app)
    readme_template = tmp_path / "readme_template.yml"
    readme_template.write_text("project: example\n")
    dtoolcore.utils.write_config_value_to_file(
        "DTOOL_README_TEMPLATE_FPATH", str(readme_template))

    with patch(_CONFIG) as mock_config:
        mock_config.lookup_url = "https://lookup.example.com"
        mock_config.token = "tok123"
        mock_config.auth_url = "https://auth.example.com"
        mock_config.verify_ssl = True
        mock_config.disable_authentication = False
        dialog._refresh_settings_dialog()

    assert dialog.lookup_url_entry.get_text() == "https://lookup.example.com"
    assert dialog.token_entry.get_text() == "tok123"
    assert dialog.authenticator_url_entry.get_text() == "https://auth.example.com"
    assert dialog.dtool_readme_template_fpath_file_chooser_button.get_filename() \
        == str(readme_template)
