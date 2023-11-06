import os
from unittest.mock import patch, MagicMock
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
