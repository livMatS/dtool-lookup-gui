import asyncio

import pytest
from unittest.mock import Mock, patch, ANY
from gi.repository import Gtk
from dtool_lookup_gui.views.main_window import MainWindow


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.mark.asyncio
async def test_do_refresh_view(app):
    with patch.object(app.main_window, 'refresh', new_callable=Mock) as mock_refresh:
        app.main_window.activate_action('refresh-view')
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_do_get_item(main_window):
    """Test do_get_item action."""
    with patch('shutil.copyfile') as mock_copyfile, \
            patch('dtool_lookup_gui.views.main_window.launch_default_app_for_uri') as mock_launch_app, \
            patch('dtool_lookup_gui.views.main_window.settings') as mock_settings, \
            patch.object(main_window, '_get_selected_items',
                         return_value=[('item', 'uuid')]) as mock_get_selected_items:
        # Set settings value
        mock_settings.open_downloaded_item = False

        # Mock value to mimic the GVariant returned by the value parameter
        value = Mock()
        value.get_string.return_value = "/path/to/destination"

        # Mock action to mimic the Gio.SimpleAction
        action = Mock()

        # Perform the get item action
        await main_window.do_get_item(action, value)

        # Assert that copyfile was called
        mock_copyfile.assert_called_once_with(ANY, "/path/to/destination")

        # Assert that _get_selected_items was called
        mock_get_selected_items.assert_called_once()

        # Optionally assert launch_default_app_for_uri call based on settings
        if mock_settings.open_downloaded_item:
            mock_launch_app.assert_called_once_with("/path/to/destination")

@pytest.mark.asyncio
async def test_do_search_select_and_show(main_window):
    """Test the do_search_select_and_show action."""

    # Mock the '_search_select_and_show' method on the MainWindow instance
    with patch.object(main_window, '_search_select_and_show', new_callable=Mock) as mock_search_select_and_show:
        # Create a mock object for the value parameter
        mock_value = Mock()
        mock_value.get_string.return_value = "test search text"

        # Mock action to mimic the Gio.SimpleAction
        mock_action = Mock()

        # Call the do_search_select_and_show method
        await main_window.do_search_select_and_show(mock_action, mock_value)

        # Assert that _search_select_and_show was called with the correct search text
        mock_search_select_and_show.assert_called_once_with("test search text")
