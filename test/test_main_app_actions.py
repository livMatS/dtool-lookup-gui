import os
from unittest.mock import patch, MagicMock
import pytest
import dtoolcore
from dtool_lookup_gui.models.settings import settings as app_settings


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'

@pytest.fixture
async def settings():
    # Store original settings
    original_settings = app_settings.get_all()

    # Define a function to restore original settings after the test
    def restore_original_settings():
        for key, value in original_settings.items():
            app_settings.set(key, value)

    # Reset settings to default or test values before the test
    app_settings.reset()

    # Yield the settings to the test function
    yield app_settings

    # Restore original settings after the test is done
    restore_original_settings()

@pytest.mark.asyncio
async def test_do_reset_config(app, settings):
    # Setup: Mock the environment variables
    mock_data = {
        "DTOOL_LOOKUP_SERVER_TOKEN": "abcd1234ef",
        "DTOOL_LOOKUP_SERVER_TOKEN_GENERATOR_URL": "https://demo.dtool.dev/token",
        "DTOOL_LOOKUP_SERVER_URL": "https://demo.dtool.dev/lookup",
        "DTOOL_LOOKUP_SERVER_VERIFY_SSL": "false",
        "DTOOL_USER_EMAIL": "test.user@example.com",
        "DTOOL_USER_FULL_NAME": "Test User"
    }
    with patch.dict(os.environ, mock_data), \
         patch('os.remove') as mock_remove, \
         patch.object(app, 'emit') as mock_emit:  # Patch the emit method

        settings.reset = MagicMock()  # Mock the settings reset method

        # Perform the reset config action
        await app.do_reset_config()

        # Assert that os.remove has been called with the correct path
        mock_remove.assert_called_once_with(dtoolcore.utils.DEFAULT_CONFIG_PATH)

        # Assert that the settings.reset was called once
        settings.reset.assert_called_once()

        # Assert that the 'dtool-config-changed' signal has been emitted
        mock_emit.assert_called_once_with('dtool-config-changed')
