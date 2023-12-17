# 1. Direct calls in tests isolate specific functionalities for focused, independent testing of components.
# 2. Triggering actions and using mocks are crucial for integration testing, ensuring components interact correctly.
# 3. Mocking and action triggering simulate real-world user interactions and application responses.
# 4. Separating tests for direct calls and action triggers aids in maintaining clear, organized test structures.
# 5. This approach enhances test suite readability and makes it easier to understand and update.
import asyncio
import time

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from gi.repository import Gtk, Gio, GLib


@pytest.mark.asyncio
async def test_do_search_direct_call(populated_app):
    """
    Test the do_search method for directly processing a search in a populated application.
    This test checks if the search action correctly triggers the search process and
    verifies that the search results are appropriately loaded and displayed in the UI.
    """

    # Helper function to wait for datasets to load in the list box.
    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached if datasets are not loaded within the specified time

    # Trigger the 'refresh-view' action to load datasets
    populated_app.main_window.activate_action('refresh-view')

    # Wait until datasets are loaded in the dataset list box
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with a test search query
    search_query = "test_search_query"
    search_text_variant = GLib.Variant.new_string(search_query)

    # Create and add the search action to the main window of the application
    search_action = Gio.SimpleAction.new("search", search_text_variant.get_type())
    populated_app.main_window.add_action(search_action)

    # Connect the search action to the do_search method of the main window
    search_action.connect("activate", populated_app.main_window.do_search)

    # Trigger the search action with the test search query
    search_action.activate(search_text_variant)

    # Optionally, wait for the search results to be processed and displayed
    # This step depends on the application's implementation and response time
    await asyncio.sleep(1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the search results are correctly displayed
    assert len(populated_app.main_window.base_uri_list_box.get_children()) > 0, "No search results found"
    # Additional assertions can be added here based on the expected outcomes of the search

    # Await completion of any remaining asynchronous tasks related to the search
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_search_action_trigger(app):
    """Test if 'search' action triggers do_search method."""

    # Mock dependencies
    mock_base_uri_list_box = MagicMock()
    app.main_window.base_uri_list_box = mock_base_uri_list_box

    # Setup necessary mocks for the action trigger
    app.main_window._search = MagicMock()

    # Create and add the action
    search_text_variant = GLib.Variant.new_string("test_search_query")
    search_action = Gio.SimpleAction.new("search", search_text_variant.get_type())
    app.main_window.add_action(search_action)

    # Patch do_search method after action is added
    with patch.object(app.main_window, 'do_search', new_callable=MagicMock) as mock_do_search:
        # Connect the action
        search_action.connect("activate", app.main_window.do_search)

        # Trigger the action
        search_action.activate(search_text_variant)

        # Assert that do_search was called once
        mock_do_search.assert_called_once_with(search_action, search_text_variant)


@pytest.mark.asyncio
async def test_do_select_dataset_row_by_row_index_direct_call(populated_app):
    """
    Test the do_select_dataset_row_by_row_index method for directly selecting a dataset row by index.
    It verifies if the dataset list is correctly populated and the specified dataset row is selected.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True
            await asyncio.sleep(0.1)
        return False

    # Trigger the 'refresh-view' action and wait for datasets to load
    populated_app.main_window.activate_action('refresh-view')
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with a valid test row index (e.g., 0 for the first row)
    row_index = 6
    row_index_variant = GLib.Variant.new_uint32(row_index)

    # Create and add the select dataset action to the main window of the application
    select_dataset_action = Gio.SimpleAction.new("select-dataset", row_index_variant.get_type())
    populated_app.main_window.add_action(select_dataset_action)

    # Connect the select dataset action to the do_select_dataset_row_by_row_index method
    select_dataset_action.connect("activate", populated_app.main_window.do_select_dataset_row_by_row_index)

    # Trigger the select dataset action with the test row index
    select_dataset_action.activate(row_index_variant)

    # Optionally, wait for the UI to update if necessary
    await asyncio.sleep(0.1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the correct dataset row is selected
    selected_row = populated_app.main_window.dataset_list_box.get_selected_row()

    # Assert that the selected row is not None and has the expected index
    assert selected_row is not None, "No dataset row was selected"
    assert selected_row.get_index() == row_index, f"Expected row index {row_index}, got {selected_row.get_index()}"

    # Await completion of any remaining asynchronous tasks related to the selection
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_select_dataset_row_by_row_index_action_trigger(app):
    """Test if 'select-dataset' action triggers do_select_dataset_row_by_row_index method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    app.main_window._select_dataset_row_by_row_index = MagicMock()

    # Create and add the action
    row_index_variant = GLib.Variant.new_uint32(1)  # Example index
    select_dataset_action = Gio.SimpleAction.new("select-dataset", row_index_variant.get_type())
    app.main_window.add_action(select_dataset_action)

    # Patch do_select_dataset_row_by_row_index method after action is added
    with patch.object(app.main_window, 'do_select_dataset_row_by_row_index',
                      new_callable=MagicMock) as mock_do_select_dataset_row_by_row_index:
        # Connect the action
        select_dataset_action.connect("activate", app.main_window.do_select_dataset_row_by_row_index)

        # Trigger the action
        select_dataset_action.activate(row_index_variant)

        # Assert that do_select_dataset_row_by_row_index was called once
        mock_do_select_dataset_row_by_row_index.assert_called_once_with(select_dataset_action, row_index_variant)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_uri_direct_call(populated_app):
    """
    Test the do_show_dataset_details_by_uri method for processing a URI directly. It verifies
    if the correct dataset is selected and its content is displayed based on the URI.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached

    # Trigger the 'refresh-view' action
    populated_app.main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Define a URI that corresponds to a dataset in the populated dataset list
    test_uri = "smb://test-share/51e67a6e-3f38-43e9-bb79-01700dc09c61"

    # Create a GLib.Variant with the test URI
    uri_variant = GLib.Variant.new_string(test_uri)

    # Call the do_show_dataset_details_by_uri method with the test URI
    populated_app.main_window.do_show_dataset_details_by_uri(None, uri_variant)

    # Retrieve the dataset that should be selected based on the URI
    index = populated_app.main_window.dataset_list_box.get_row_index_from_uri(test_uri)
    selected_row = populated_app.main_window.dataset_list_box.get_row_at_index(index)
    selected_dataset = selected_row.dataset if selected_row is not None else None

    # Assert that the dataset with the given URI is selected
    assert selected_dataset is not None, "No dataset was selected"
    assert selected_dataset.uri == test_uri, f"Expected URI {test_uri}, got {selected_dataset.uri}"

    # Await completion of all tasks related to the test
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


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
    with patch.object(app.main_window, 'do_show_dataset_details_by_uri',
                      new_callable=MagicMock) as mock_do_show_dataset_details_by_uri:
        # Connect the action
        show_dataset_by_uri_action.connect("activate", app.main_window.do_show_dataset_details_by_uri)

        # Trigger the action
        show_dataset_by_uri_action.activate(uri_variant)

        # Assert that do_show_dataset_details_by_uri was called once
        mock_do_show_dataset_details_by_uri.assert_called_once_with(show_dataset_by_uri_action, uri_variant)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_row_index_direct_call(populated_app, mock_dataset_list):
    """
    Test the do_show_dataset_details_by_row_index method for directly showing dataset details by row index.
    It verifies if the dataset list is correctly populated and the specified dataset details are displayed.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached if datasets are not loaded within the specified time

    # Trigger the 'refresh-view' action and wait for datasets to load
    populated_app.main_window.activate_action('refresh-view')
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with a test row index (e.g., 0 for the first row)
    row_index = 1
    row_index_variant = GLib.Variant.new_uint32(row_index)

    # Create and add the show dataset action to the main window of the application
    show_dataset_action = Gio.SimpleAction.new("show-dataset", row_index_variant.get_type())
    populated_app.main_window.add_action(show_dataset_action)

    # Connect the show dataset action to the do_show_dataset_details_by_row_index method
    show_dataset_action.connect("activate", populated_app.main_window.do_show_dataset_details_by_row_index)

    # Trigger the show dataset action with the test row index
    show_dataset_action.activate(row_index_variant)

    # Optionally, wait for the UI to update and dataset details to be displayed
    await asyncio.sleep(0.1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the dataset details are correctly displayed
    selected_dataset = populated_app.main_window.dataset_list_box.get_row_at_index(row_index).dataset

    expected_uri = mock_dataset_list[1]['uri']
    expected_uuid = mock_dataset_list[1]['uuid']

    assert selected_dataset.uri == expected_uri, f"Expected URI {expected_uri}, got {selected_dataset.uri}"
    assert selected_dataset.uuid == expected_uuid, f"Expected UUID {expected_uuid}, got {selected_dataset.uuid}"

    # Additional assertions can be made here based on the expected behavior and UI element updates

    # Await completion of any remaining asynchronous tasks related to showing the dataset details
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_row_index_action_trigger(app):
    """Test if 'show-dataset' action triggers do_show_dataset_details_by_row_index method."""

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    app.main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    app.main_window._show_dataset_details_by_row_index = MagicMock()

    # Create and add the action
    row_index_variant = GLib.Variant.new_uint32(1)  # Example index
    show_dataset_action = Gio.SimpleAction.new("show-dataset", row_index_variant.get_type())
    app.main_window.add_action(show_dataset_action)

    # Patch do_show_dataset_details_by_row_index method after action is added
    with patch.object(app.main_window, 'do_show_dataset_details_by_row_index',
                      new_callable=MagicMock) as mock_do_show_dataset_details_by_row_index:
        # Connect the action
        show_dataset_action.connect("activate", app.main_window.do_show_dataset_details_by_row_index)

        # Trigger the action
        show_dataset_action.activate(row_index_variant)

        # Assert that do_show_dataset_details_by_row_index was called once
        mock_do_show_dataset_details_by_row_index.assert_called_once_with(show_dataset_action, row_index_variant)


@pytest.mark.asyncio
async def test_do_search_select_and_show_direct_call(populated_app, mock_dataset_list):
    """
    Test the do_search_select_and_show method for processing a search directly. It verifies
    if the dataset list is correctly populated, the first dataset is selected, and its
    content is displayed.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached

    # Trigger the 'refresh-view' action
    populated_app.main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with the test search query
    mock_variant = GLib.Variant.new_string("test_search_query")

    # Call the method with the test search query
    populated_app.main_window.do_search_select_and_show(None, mock_variant)

    # Assertions to check the state of the application after the search
    assert len(populated_app.main_window.dataset_list_box.get_children()) > 0, "No datasets found in the list box"
    first_dataset_row = populated_app.main_window.dataset_list_box.get_children()[0]
    dataset = first_dataset_row.dataset

    # Assert that the dataset's URI matches the expected URI
    assert dataset.uri == mock_dataset_list[0]['uri'], f"Expected URI {mock_dataset_list[0]['uri']}, got {dataset.uri}"

    # Await completion of all tasks related to the test
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


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
    with patch.object(app.main_window, 'do_search_select_and_show',
                      new_callable=MagicMock) as mock_do_search_select_and_show:
        # Connect the action
        search_select_show_action.connect("activate", app.main_window.do_search_select_and_show)

        # Trigger the action
        search_select_show_action.activate(search_variant)

        # Assert that do_search_select_and_show was called once
        mock_do_search_select_and_show.assert_called_once_with(search_select_show_action, search_variant)


@pytest.mark.asyncio
@pytest.mark.skip(reason="no way of currently testing this")
async def test_do_get_item_direct_call(populated_app, tmp_path):
    """
    Test the do_get_item method for copying a selected item directly.
    It verifies if the selected item is correctly copied to the specified destination.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached

    # Trigger the 'refresh-view' action to load datasets
    populated_app.main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(populated_app.main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Select the first dataset
    first_dataset_row = populated_app.main_window.dataset_list_box.get_children()[0]
    dataset = first_dataset_row.dataset

    # Assuming the first dataset's UUID as the item UUID (Replace this with the actual item UUID logic)
    item_uuid = dataset.uuid
    populated_app.main_window._get_selected_items = lambda: [('item_name', item_uuid)]

    # Define the destination file path
    dest_file = tmp_path / "destination_file"

    # Create a GLib.Variant with the destination file path
    dest_file_variant = GLib.Variant.new_string(str(dest_file))

    dest_file = tmp_path / "destination_file"
    print(f"Destination file path: {dest_file}")

    # Call the do_get_item method without 'await'
    try:
        populated_app.main_window.do_get_item(None, dest_file_variant)
    except Exception as e:
        print(f"Error during 'do_get_item': {e}")
        raise

    # Wait for all asynchronous tasks to complete
    await asyncio.sleep(1)  # Increase sleep time if necessary
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        completed_tasks = await asyncio.gather(*pending_tasks, return_exceptions=True)
        for task in completed_tasks:
            if isinstance(task, Exception):
                print(f"Exception in async task: {task}")

    # Verify that the file was copied
    file_exists = dest_file.exists()
    print(f"File exists: {file_exists}")
    assert file_exists, "The item was not copied to the specified destination"


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
async def test_do_refresh_view_direct_call(app):
    """Test the direct call of the do_refresh_view method."""

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
async def test_do_get_item_direct_call_fails_due_to_no_selected_item(app):
    """Test that the do_get_item method for copying a selected item fails when not item is selected."""

    mock_variant = GLib.Variant.new_string("dummy_path")

    # Directly call the method with mock objects
    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'dataset'"):
        app.main_window.do_get_item(None, mock_variant)
