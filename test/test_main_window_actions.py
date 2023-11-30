import pytest
from unittest.mock import patch, Mock, MagicMock
import asyncio
from gi.repository import Gtk, Gio, GLib
from dtool_lookup_gui.views.main_window import MainWindow
from unittest.mock import patch, MagicMock, AsyncMock




@pytest.mark.asyncio
async def test_do_refresh_view(app):
    """Test the do_refresh_view method triggers the refresh method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box


    app.main_window.do_refresh_view(None, None)
    # Assertions for side effects (if applicable)


    # Patch the main window's refresh method
    with patch.object(app.main_window, 'refresh', new_callable=Mock) as mock_refresh:
        app.main_window.activate_action('refresh-view')
        mock_refresh.assert_called_once()

        # Check if get_selected_row was called on dataset_list_box
        mock_dataset_list_box.get_selected_row.assert_called_once()


from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_do_get_item(app):
    """Test the do_get_item method for copying a selected item."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box
    mock_settings = MagicMock()
    app.main_window.settings = mock_settings

    # Mock _get_selected_items to return one item
    app.main_window._get_selected_items = MagicMock(return_value=[('item_name', 'item_uuid')])

    # Create a mock action and variant
    mock_action = MagicMock(spec=Gio.SimpleAction)
    mock_variant = GLib.Variant.new_string("dummy_path")

    # Mock async call in do_get_item
    mock_dataset = MagicMock()
    mock_dataset.get_item = AsyncMock()  # Use AsyncMock for async calls
    mock_dataset_list_box.get_selected_row.return_value = MagicMock(dataset=mock_dataset)

    # Call the method with mock objects
    app.main_window.do_get_item(mock_action, mock_variant)
    # Use patch.object to mock do_get_item method


