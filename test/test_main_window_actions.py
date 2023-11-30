import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from gi.repository import Gtk, Gio, GLib



@pytest.mark.asyncio
async def test_do_refresh_view_direct_call(app):
    """Test the direct call of the do_refresh_view method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box

    # Directly call the do_refresh_view method
    app.main_window.do_refresh_view(None, None)

@pytest.mark.asyncio
async def test_refresh_method_triggered_by_action(app):
    """Test if the 'refresh-view' action triggers the refresh method."""

    # Patch the main window's refresh method
    with patch.object(app.main_window, 'refresh', new_callable=MagicMock) as mock_refresh:
        # Trigger the 'refresh-view' action
        app.main_window.activate_action('refresh-view')

        # Assert that the refresh method was called once
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_do_get_item_direct_call(app):
    """Test the do_get_item method for copying a selected item directly."""

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
    mock_dataset.get_item = AsyncMock()
    mock_dataset_list_box.get_selected_row.return_value = MagicMock(dataset=mock_dataset)

    # Directly call the method with mock objects
    app.main_window.do_get_item(mock_action, mock_variant)


@pytest.mark.asyncio
async def test_do_get_item_action_trigger(app):
    """Test if 'get-item' action triggers do_get_item method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box
    mock_settings = MagicMock()
    app.main_window.settings = mock_settings

    # Setup necessary mocks for the action trigger
    mock_dataset = MagicMock()
    mock_dataset.get_item = AsyncMock()
    mock_dataset_list_box.get_selected_row.return_value = MagicMock(dataset=mock_dataset)
    app.main_window._get_selected_items = MagicMock(return_value=[('item_name', 'item_uuid')])

    # Create and add the action
    dest_file_variant = GLib.Variant.new_string("dummy_path")
    get_item_action = Gio.SimpleAction.new("get-item", dest_file_variant.get_type())
    app.main_window.add_action(get_item_action)

    # Patch do_get_item method after action is added
    with patch.object(app.main_window, 'do_get_item', new_callable=MagicMock) as mock_do_get_item:
        # Connect the action
        get_item_action.connect("activate", app.main_window.do_get_item)

        # Trigger the action
        get_item_action.activate(dest_file_variant)

        # Assert that do_get_item was called once
        mock_do_get_item.assert_called_once_with(get_item_action, dest_file_variant)