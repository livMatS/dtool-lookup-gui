#
# Copyright 2023 Ashwin Vazhappilly
#           2022-2023 Johannes Laurin Hörmann
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
import json
import logging
import types
from unittest import mock
from unittest.mock import patch, mock_open, MagicMock, ANY, AsyncMock
import pytest
import dtoolcore

from dtool_lookup_gui.models.settings import settings as app_settings
from dtool_lookup_api.core.LookupClient import authenticate


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.fixture
def settings():
    """Provide test case with app settings."""
    yield app_settings


@pytest.mark.asyncio
async def test_do_toggle_logging(app):
    """Test do_toggle_logging action."""

    with patch('logging.disable') as mock_logging_disable:
        # Mock value to mimic the GVariant returned by the value parameter
        value = MagicMock()
        value.get_boolean.return_value = True  # Testing the True case

        # Mock action to mimic the Gio.SimpleAction
        action = MagicMock()

        # Perform the toggle logging action for enabling logging
        app.do_toggle_logging(action, value)

        # Assert that logging.disable was called with logging.NOTSET
        mock_logging_disable.assert_called_once_with(logging.NOTSET)
        action.set_state.assert_called_once_with(value)

        # Reset mocks to test the False case
        mock_logging_disable.reset_mock()
        action.set_state.reset_mock()
        value.get_boolean.return_value = False

        # Perform the toggle logging action for disabling logging
        app.do_toggle_logging(action, value)

        # Assert that logging.disable was called with logging.WARNING
        mock_logging_disable.assert_called_once_with(logging.WARNING)
        action.set_state.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_do_set_loglevel(app):
    """Test do_set_loglevel action."""

    with patch.object(logging.getLogger(), 'setLevel') as mock_set_level:
        # Mock values for loglevel
        loglevel = 20  # Example log level (e.g., logging.INFO)

        # Mock value to mimic the GVariant returned by the value parameter
        value = MagicMock()
        value.get_uint16.return_value = loglevel

        # Mock action to mimic the Gio.SimpleAction
        action = MagicMock()
        action_state = MagicMock()
        action_state.get_uint16.return_value = 0
        action.get_state.return_value = action_state

        # Perform the set loglevel action
        app.do_set_loglevel(action, value)

        # Assert that the root logger's setLevel was called with the correct level
        mock_set_level.assert_called_once_with(loglevel)
        action.set_state.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_do_set_logfile(app):
    """Test do_set_logfile action."""
    with patch('logging.FileHandler') as mock_file_handler, \
            patch.object(logging.getLogger(), 'addHandler') as mock_add_handler:
        # Mock values for logfile
        logfile = "/path/to/logfile.log"

        # Mock value to mimic the GVariant returned by the value parameter
        value = MagicMock()
        value.get_string.return_value = logfile

        # Mock action to mimic the Gio.SimpleAction
        action = MagicMock()
        action_state = MagicMock()
        action_state.get_string.return_value = ""
        action.get_state.return_value = action_state

        # Perform the set logfile action
        app.do_set_logfile(action, value)

        # Assert that logging.FileHandler was called with the correct path
        mock_file_handler.assert_called_once_with(logfile)

        # Assert that the FileHandler was added to the root logger
        mock_add_handler.assert_called_once_with(ANY)

        # Assert that the action's state was set to the new logfile value
        action.set_state.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_do_reset_config(app, settings):
    """Test do_reset_config action."""
    with patch('os.remove') as mock_remove, \
            patch.object(app, 'emit') as mock_emit:  # Patch the emit method

        settings.reset = MagicMock()  # Mock the settings reset method

        # Perform the reset config action
        app.activate_action('reset-config')

        # The 'do_reset_config' action removes and replaces the dtool.json
        # config file.
        # Assert that os.remove has been called with the correct path
        mock_remove.assert_called_once_with(dtoolcore.utils.DEFAULT_CONFIG_PATH)

        # The 'do_reset_config' action calls the reset method on the
        # Gio.Setting property of the settings object.
        # Assert that the settings.reset was called once.
        settings.reset.assert_called_once()

        # The emit method is called when a signal is emitted.
        # The 'do_reset_config' action is expected to emit a
        # 'dtool-config-changed' signal.
        # Assert that the 'dtool-config-changed' signal has been emitted
        mock_emit.assert_called_once_with('dtool-config-changed')


@pytest.mark.asyncio
async def test_do_import_config(app, settings):
    """Test do_import_config action."""
    mock_config = {'key1': 'value1', 'key2': 'value2'}
    # Define the mock config file path
    config_file_path = '/path/to/mock/config.json'

    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))) as mock_file, \
            patch('json.load', return_value=mock_config), \
            patch('dtoolcore.utils.write_config_value_to_file') as mock_write_config, \
            patch.object(app, 'emit') as mock_emit:
        # Create a mock for the GLib.Variant object
        mock_value = mock.Mock()
        mock_value.get_string.return_value = config_file_path

        # Perform the import config action
        app.do_import_config('import-config', mock_value)

        # Assert that the config file is opened correctly with the specified path
        mock_file.assert_any_call(config_file_path, 'r')

        # Assert that the config values are written to file
        for key, value in mock_config.items():
            mock_write_config.assert_any_call(key, value)

        # Assert that the 'dtool-config-changed' signal has been emitted
        mock_emit.assert_called_once_with('dtool-config-changed')


@pytest.mark.asyncio
async def test_do_export_config(app, settings):
    """Test do_export_config action."""
    mock_config = {'key1': 'value1', 'key2': 'value2'}
    # Define the mock config file path
    config_file_path = '/path/to/mock/config.json'

    # Setup mock open
    mock_file_handle = mock_open()
    with patch('builtins.open', mock_file_handle) as mock_file, \
            patch('dtoolcore.utils._get_config_dict_from_file', return_value=mock_config), \
            patch.object(app, 'emit') as mock_emit:
        # Create a mock for the GLib.Variant object
        mock_value = mock.Mock()
        mock_value.get_string.return_value = config_file_path

        # Perform the export config action
        app.do_export_config('export-config', mock_value)

        # Assert that the config file is opened correctly with the specified path
        mock_file.assert_called_once_with(config_file_path, 'w')

        # Concatenate all the calls to write and compare with expected JSON
        written_data = ''.join(call_arg.args[0] for call_arg in mock_file_handle().write.call_args_list)
        expected_file_content = json.dumps(mock_config, indent=4)
        assert written_data == expected_file_content


@pytest.mark.asyncio
async def test_do_renew_token(app):
    """Test do_renew_token action."""
    with patch('asyncio.create_task') as mock_create_task, \
         patch.object(app, 'emit') as mock_emit:  # Patch the emit method

        # Mock values for username, password, and auth_url
        username = "testuser"
        password = "testpass"
        auth_url = "http://auth.example.com"

        # Tuple variant to mimic the value parameter in the method
        value = MagicMock()
        value.unpack.return_value = (username, password, auth_url)

        # Perform the renew token action
        app.do_renew_token(None, value)

        # Assert that asyncio.create_task was called with the retrieve_token coroutine
        mock_create_task.assert_called_once()
        args, kwargs = mock_create_task.call_args
        retrieve_token_coro = args[0]
        assert isinstance(retrieve_token_coro, types.CoroutineType)

        # Assert that the coroutine was called with the correct arguments
        assert retrieve_token_coro.cr_code.co_name == 'retrieve_token'
        assert retrieve_token_coro.cr_frame.f_locals['auth_url'] == auth_url
        assert retrieve_token_coro.cr_frame.f_locals['username'] == username
        assert retrieve_token_coro.cr_frame.f_locals['password'] == password

        # The 'do_renew_token' action is expected to emit a
        # 'dtool-config-changed' signal after successful token renewal.
        # Since the actual token retrieval is asynchronous and mocked,
        # we cannot assert this directly in this test.
        # mock_emit.assert_called_once_with('dtool-config-changed')