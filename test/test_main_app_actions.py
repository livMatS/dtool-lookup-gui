import os
import json
from unittest import mock
from unittest.mock import patch, mock_open, Mock, MagicMock

import pytest
import dtoolcore

from dtool_lookup_gui.models.settings import settings as app_settings



@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.fixture
def settings():
    """Provide test case with app settings."""
    yield app_settings


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

