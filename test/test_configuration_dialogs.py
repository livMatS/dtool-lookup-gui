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
"""Unit tests for the S3 and SMB base-URI configuration dialogs.

These Gtk.Window dialogs are self-contained (their __init__ does not touch the
application), so they are constructed directly. They read and write the dtool
config through dtoolcore, which conftest.py isolates to a per-process temp file.
"""
from unittest.mock import MagicMock

from dtoolcore.utils import get_config_value, write_config_value_to_file

from dtool_lookup_gui.views.s3_configuration_dialog import S3ConfigurationDialog
from dtool_lookup_gui.views.smb_configuration_dialog import SMBConfigurationDialog


# ===========================================================================
# S3ConfigurationDialog
# ===========================================================================

def test_s3_dialog_blank_when_no_bucket():
    dialog = S3ConfigurationDialog()
    assert dialog.bucket_entry.get_text() == ""
    assert dialog.bucket_entry.get_sensitive() is True


def test_s3_dialog_prefills_from_config_and_locks_bucket():
    write_config_value_to_file("DTOOL_S3_ENDPOINT_prefill", "https://s3.example.com")
    write_config_value_to_file("DTOOL_S3_ACCESS_KEY_ID_prefill", "AKIA")

    dialog = S3ConfigurationDialog(bucket="prefill")

    assert dialog.bucket_entry.get_text() == "prefill"
    assert dialog.bucket_entry.get_sensitive() is False  # locked once known
    assert dialog.endpoint_url_entry.get_text() == "https://s3.example.com"
    assert dialog.access_key_entry.get_text() == "AKIA"


def test_s3_dialog_apply_writes_config_and_calls_back():
    apply = MagicMock()
    dialog = S3ConfigurationDialog(apply=apply)
    dialog.bucket_entry.set_text("applied")
    dialog.endpoint_url_entry.set_text("https://endpoint")
    dialog.access_key_entry.set_text("key-id")
    dialog.secret_key_entry.set_text("secret")
    dialog.prefix_entry.set_text("u/")

    dialog.on_apply_clicked(None)

    assert get_config_value("DTOOL_S3_ENDPOINT_applied") == "https://endpoint"
    assert get_config_value("DTOOL_S3_ACCESS_KEY_ID_applied") == "key-id"
    assert get_config_value("DTOOL_S3_SECRET_ACCESS_KEY_applied") == "secret"
    assert get_config_value("DTOOL_S3_DATASET_PREFIX_applied") == "u/"
    apply.assert_called_once()


def test_s3_dialog_cancel_does_not_write_config():
    dialog = S3ConfigurationDialog()
    dialog.bucket_entry.set_text("cancelled")
    dialog.endpoint_url_entry.set_text("https://nope")
    dialog.on_cancel_clicked(None)
    assert get_config_value("DTOOL_S3_ENDPOINT_cancelled") is None


# ===========================================================================
# SMBConfigurationDialog
# ===========================================================================

def test_smb_dialog_blank_when_no_name():
    dialog = SMBConfigurationDialog()
    assert dialog.name_entry.get_text() == ""
    assert dialog.name_entry.get_sensitive() is True


def test_smb_dialog_prefills_from_config_and_locks_name():
    write_config_value_to_file("DTOOL_SMB_SERVER_NAME_prefillsmb", "fileserver")
    write_config_value_to_file("DTOOL_SMB_SERVER_PORT_prefillsmb", 139)

    dialog = SMBConfigurationDialog(name="prefillsmb")

    assert dialog.name_entry.get_text() == "prefillsmb"
    assert dialog.name_entry.get_sensitive() is False
    assert dialog.server_name_entry.get_text() == "fileserver"
    assert dialog.server_port_entry.get_text() == "139"


def test_smb_dialog_default_port_when_unset():
    # The port field falls back to 445 when no config value exists.
    dialog = SMBConfigurationDialog(name="noport")
    assert dialog.server_port_entry.get_text() == "445"


def test_smb_dialog_apply_writes_config_and_calls_back():
    apply = MagicMock()
    dialog = SMBConfigurationDialog(apply=apply)
    dialog.name_entry.set_text("smbapplied")
    dialog.server_name_entry.set_text("server")
    dialog.server_port_entry.set_text("445")
    dialog.service_name_entry.set_text("share")
    dialog.path_entry.set_text("/data")
    dialog.domain_entry.set_text("WORKGROUP")
    dialog.username_entry.set_text("alice")
    dialog.password_entry.set_text("secret")

    dialog.on_apply_clicked(None)

    assert get_config_value("DTOOL_SMB_SERVER_NAME_smbapplied") == "server"
    # The port is stored as an int.
    assert get_config_value("DTOOL_SMB_SERVER_PORT_smbapplied") == 445
    assert get_config_value("DTOOL_SMB_SERVICE_NAME_smbapplied") == "share"
    assert get_config_value("DTOOL_SMB_USERNAME_smbapplied") == "alice"
    apply.assert_called_once()


def test_smb_dialog_cancel_does_not_write_config():
    dialog = SMBConfigurationDialog()
    dialog.name_entry.set_text("smbcancelled")
    dialog.server_name_entry.set_text("nope")
    dialog.on_cancel_clicked(None)
    assert get_config_value("DTOOL_SMB_SERVER_NAME_smbcancelled") is None
