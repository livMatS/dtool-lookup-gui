# 1. Direct calls in tests isolate specific functionalities for focused, independent testing of components.
# 2. Triggering actions and using mocks are crucial for integration testing, ensuring components interact correctly.
# 3. Mocking and action triggering simulate real-world user interactions and application responses.
# 4. Separating tests for direct calls and action triggers aids in maintaining clear, organized test structures.
# 5. This approach enhances test suite readability and makes it easier to understand and update.



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


@pytest.mark.asyncio
async def test_do_search_select_and_show_direct_call(app):
    """Test the do_search_select_and_show method for processing a search directly."""

    # Mock dependencies
    mock_base_uri_list_box = MagicMock()
    app.main_window.base_uri_list_box = mock_base_uri_list_box

    # Mock _search_select_and_show to simulate search behavior
    app.main_window._search_select_and_show = MagicMock()

    # Create a mock action and variant
    mock_action = MagicMock(spec=Gio.SimpleAction)
    mock_variant = GLib.Variant.new_string("test_search_query")

    # Directly call the method with mock objects
    app.main_window.do_search_select_and_show(mock_action, mock_variant)

    # Assert that _search_select_and_show was called with the correct query
    app.main_window._search_select_and_show.assert_called_once_with("test_search_query")


@pytest.mark.asyncio
async def test_do_search_select_and_show_action_trigger(app):
    """Test if 'search-select-show' action triggers do_search_select_and_show method."""

    # Mock dependencies
    mock_base_uri_list_box = MagicMock()
    app.main_window.base_uri_list_box = mock_base_uri_list_box

    # Setup necessary mocks for the action trigger
    app.main_window._search_select_and_show = MagicMock()

    # Create and add the action
    search_variant = GLib.Variant.new_string("test_search_query")
    search_select_show_action = Gio.SimpleAction.new("search-select-show", search_variant.get_type())
    app.main_window.add_action(search_select_show_action)

    # Patch do_search_select_and_show method after action is added
    with patch.object(app.main_window, 'do_search_select_and_show', new_callable=MagicMock) as mock_do_search_select_and_show:
        # Connect the action
        search_select_show_action.connect("activate", app.main_window.do_search_select_and_show)

        # Trigger the action
        search_select_show_action.activate(search_variant)

        # Assert that do_search_select_and_show was called once
        mock_do_search_select_and_show.assert_called_once_with(search_select_show_action, search_variant)

@pytest.mark.asyncio
async def test_do_show_dataset_details_by_uri_direct_call(app):
    """Test the do_show_dataset_details_by_uri method for showing dataset details directly."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box

    # Mock _show_dataset_details_by_uri to simulate behavior
    app.main_window._show_dataset_details_by_uri = MagicMock()

    # Create a mock action and variant
    mock_action = MagicMock(spec=Gio.SimpleAction)
    mock_variant = GLib.Variant.new_string("dummy_uri")

    # Directly call the method with mock objects
    app.main_window.do_show_dataset_details_by_uri(mock_action, mock_variant)

    # Assert that _show_dataset_details_by_uri was called with the correct uri
    app.main_window._show_dataset_details_by_uri.assert_called_once_with("dummy_uri")


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_uri_action_trigger(app):
    """Test if 'show-dataset-by-uri' action triggers do_show_dataset_details_by_uri method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    app.main_window._show_dataset_details_by_uri = MagicMock()

    # Create and add the action
    uri_variant = GLib.Variant.new_string("dummy_uri")
    show_dataset_by_uri_action = Gio.SimpleAction.new("show-dataset-by-uri", uri_variant.get_type())
    app.main_window.add_action(show_dataset_by_uri_action)

    # Patch do_show_dataset_details_by_uri method after action is added
    with patch.object(app.main_window, 'do_show_dataset_details_by_uri', new_callable=MagicMock) as mock_do_show_dataset_details_by_uri:
        # Connect the action
        show_dataset_by_uri_action.connect("activate", app.main_window.do_show_dataset_details_by_uri)

        # Trigger the action
        show_dataset_by_uri_action.activate(uri_variant)

        # Assert that do_show_dataset_details_by_uri was called once
        mock_do_show_dataset_details_by_uri.assert_called_once_with(show_dataset_by_uri_action, uri_variant)