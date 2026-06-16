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
import asyncio
import logging
import time
from pathlib import Path

import dtoolcore
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from gi.repository import Gtk, Gio, GLib

from dtool_lookup_gui.views.main_window import MainWindow
@pytest.mark.asyncio
async def test_do_search_direct_call(populated_app_with_mock_data):
    """
    Test the do_search method for directly processing a search in a populated application.
    This test checks if the search action correctly triggers the search process and
    verifies that the search results are appropriately loaded and displayed in the UI.
    """

    # Helper function to wait for datasets to load in the list box.
    async def wait_for_datasets_to_load(list_box, timeout=100):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached if datasets are not loaded within the specified time

    # Get main window of application
    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action to load datasets
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded in the dataset list box
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with a test search query
    search_query = "test_search_query"
    search_text_variant = GLib.Variant.new_string(search_query)

    # Create and add the search action to the main window of the application
    search_action = Gio.SimpleAction.new("search", search_text_variant.get_type())
    main_window.add_action(search_action)

    # Connect the search action to the do_search method of the main window
    search_action.connect("activate", main_window.do_search)

    # Trigger the search action with the test search query
    search_action.activate(search_text_variant)

    # Optionally, wait for the search results to be processed and displayed
    # This step depends on the application's implementation and response time
    await asyncio.sleep(1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the search results are correctly displayed
    assert len(main_window.base_uri_list_box.get_children()) > 0, "No search results found"
    # Additional assertions can be added here based on the expected outcomes of the search

    # Await completion of any remaining asynchronous tasks related to the search
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_search_action_trigger(running_app):
    """Test if 'search' action triggers do_search method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Setup necessary mocks for the action trigger
    main_window._search = MagicMock()

    # Create and add the action
    search_text_variant = GLib.Variant.new_string("test_search_query")
    search_action = Gio.SimpleAction.new("search", search_text_variant.get_type())
    main_window.add_action(search_action)

    # Patch do_search method after action is added
    with patch.object(main_window, 'do_search', new_callable=MagicMock) as mock_do_search:
        # Connect the action
        search_action.connect("activate", main_window.do_search)

        # Trigger the action
        search_action.activate(search_text_variant)

        # Assert that do_search was called once
        mock_do_search.assert_called_once_with(search_action, search_text_variant)


@pytest.mark.asyncio
async def test_do_select_dataset_row_by_row_index_direct_call(populated_app_with_mock_data):
    """
    Test the do_select_dataset_row_by_row_index method for directly selecting a dataset row by index.
    It verifies if the dataset list is correctly populated and the specified dataset row is selected.
    """

    async def wait_for_datasets_to_load(list_box, min_count=1, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) >= min_count:
                return True
            await asyncio.sleep(0.1)
        return False

    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Select row index 6, so wait until at least 7 rows have populated; waiting
    # only for ">0" raced the selection ahead of the full load on slower runners.
    row_index = 6

    # Trigger the 'refresh-view' action and wait for datasets to load
    main_window.activate_action('refresh-view')
    datasets_loaded = await wait_for_datasets_to_load(
        main_window.dataset_list_box, min_count=row_index + 1)
    assert datasets_loaded, "Datasets were not loaded in time"
    row_index_variant = GLib.Variant.new_uint32(row_index)

    # Create and add the select dataset action to the main window of the application
    select_dataset_action = Gio.SimpleAction.new("select-dataset", row_index_variant.get_type())
    main_window.add_action(select_dataset_action)

    # Connect the select dataset action to the do_select_dataset_row_by_row_index method
    select_dataset_action.connect("activate", main_window.do_select_dataset_row_by_row_index)

    # Trigger the select dataset action with the test row index
    select_dataset_action.activate(row_index_variant)

    # Optionally, wait for the UI to update if necessary
    await asyncio.sleep(0.1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the correct dataset row is selected
    selected_row = main_window.dataset_list_box.get_selected_row()

    # Assert that the selected row is not None and has the expected index
    assert selected_row is not None, "No dataset row was selected"
    assert selected_row.get_index() == row_index, f"Expected row index {row_index}, got {selected_row.get_index()}"

    # Await completion of any remaining asynchronous tasks related to the selection
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_select_dataset_row_by_row_index_action_trigger(running_app):
    """Test if 'select-dataset' action triggers do_select_dataset_row_by_row_index method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    main_window._select_dataset_row_by_row_index = MagicMock()

    # Create and add the action
    row_index_variant = GLib.Variant.new_uint32(1)  # Example index
    select_dataset_action = Gio.SimpleAction.new("select-dataset", row_index_variant.get_type())
    main_window.add_action(select_dataset_action)

    # Patch do_select_dataset_row_by_row_index method after action is added
    with patch.object(main_window, 'do_select_dataset_row_by_row_index',
                      new_callable=MagicMock) as mock_do_select_dataset_row_by_row_index:
        # Connect the action
        select_dataset_action.connect("activate", main_window.do_select_dataset_row_by_row_index)

        # Trigger the action
        select_dataset_action.activate(row_index_variant)

        # Assert that do_select_dataset_row_by_row_index was called once
        mock_do_select_dataset_row_by_row_index.assert_called_once_with(select_dataset_action, row_index_variant)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_uri_direct_call(populated_app_with_mock_data):
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

    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Define a URI that corresponds to a dataset in the populated dataset list
    test_uri = "s3://test-bucket/1a1f9fad-8589-413e-9602-5bbd66bfe675"

    # Create a GLib.Variant with the test URI
    uri_variant = GLib.Variant.new_string(test_uri)

    # Call the do_show_dataset_details_by_uri method with the test URI
    main_window.do_show_dataset_details_by_uri(None, uri_variant)

    # Retrieve the dataset that should be selected based on the URI
    index = main_window.dataset_list_box.get_row_index_from_uri(test_uri)
    selected_row = main_window.dataset_list_box.get_row_at_index(index)
    selected_dataset = selected_row.dataset if selected_row is not None else None

    # Assert that the dataset with the given URI is selected
    assert selected_dataset is not None, "No dataset was selected"
    assert selected_dataset.uri == test_uri, f"Expected URI {test_uri}, got {selected_dataset.uri}"

    # Await completion of all tasks related to the test
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_uri_action_trigger(running_app):
    """Test if 'show-dataset-by-uri' action triggers do_show_dataset_details_by_uri method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    main_window._show_dataset_details_by_uri = MagicMock()

    # Create and add the action
    uri_variant = GLib.Variant.new_string("dummy_uri")
    show_dataset_by_uri_action = Gio.SimpleAction.new("show-dataset-by-uri", uri_variant.get_type())
    main_window.add_action(show_dataset_by_uri_action)

    # Patch do_show_dataset_details_by_uri method after action is added
    with patch.object(main_window, 'do_show_dataset_details_by_uri',
                      new_callable=MagicMock) as mock_do_show_dataset_details_by_uri:
        # Connect the action
        show_dataset_by_uri_action.connect("activate", main_window.do_show_dataset_details_by_uri)

        # Trigger the action
        show_dataset_by_uri_action.activate(uri_variant)

        # Assert that do_show_dataset_details_by_uri was called once
        mock_do_show_dataset_details_by_uri.assert_called_once_with(show_dataset_by_uri_action, uri_variant)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_row_index_direct_call(populated_app_with_mock_data, mock_get_datasets):
    """
    Test the do_show_dataset_details_by_row_index method for directly showing dataset details by row index.
    It verifies if the dataset list is correctly populated and the specified dataset details are displayed.
    """

    async def wait_for_datasets_to_load(list_box, min_count=1, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) >= min_count:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)  # Yield control to allow other async tasks to run
        return False  # Timeout reached if datasets are not loaded within the specified time

    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Create a GLib.Variant with a test row index (e.g., 0 for the first row)
    row_index = 1

    # Trigger the 'refresh-view' action and wait for enough datasets to load
    main_window.activate_action('refresh-view')
    datasets_loaded = await wait_for_datasets_to_load(
        main_window.dataset_list_box, min_count=row_index + 1)
    assert datasets_loaded, "Datasets were not loaded in time"
    row_index_variant = GLib.Variant.new_uint32(row_index)

    # Create and add the show dataset action to the main window of the application
    show_dataset_action = Gio.SimpleAction.new("show-dataset", row_index_variant.get_type())
    main_window.add_action(show_dataset_action)

    # Connect the show dataset action to the do_show_dataset_details_by_row_index method
    show_dataset_action.connect("activate", main_window.do_show_dataset_details_by_row_index)

    # Trigger the show dataset action with the test row index
    show_dataset_action.activate(row_index_variant)

    # Optionally, wait for the UI to update and dataset details to be displayed
    await asyncio.sleep(0.1)  # Adjust this sleep duration as needed

    # Perform assertions to verify that the dataset details are correctly displayed
    selected_dataset = main_window.dataset_list_box.get_row_at_index(row_index).dataset

    expected_uri = mock_get_datasets[1]['uri']
    expected_uuid = mock_get_datasets[1]['uuid']

    assert selected_dataset.uri == expected_uri, f"Expected URI {expected_uri}, got {selected_dataset.uri}"
    assert selected_dataset.uuid == expected_uuid, f"Expected UUID {expected_uuid}, got {selected_dataset.uuid}"

    # Additional assertions can be made here based on the expected behavior and UI element updates

    # Await completion of any remaining asynchronous tasks related to showing the dataset details
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_show_dataset_details_by_row_index_action_trigger(running_app):
    """Test if 'show-dataset' action triggers do_show_dataset_details_by_row_index method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    main_window.dataset_list_box = mock_dataset_list_box

    # Setup necessary mocks for the action trigger
    main_window._show_dataset_details_by_row_index = MagicMock()

    # Create and add the action
    row_index_variant = GLib.Variant.new_uint32(1)  # Example index
    show_dataset_action = Gio.SimpleAction.new("show-dataset", row_index_variant.get_type())
    main_window.add_action(show_dataset_action)

    # Patch do_show_dataset_details_by_row_index method after action is added
    with patch.object(main_window, 'do_show_dataset_details_by_row_index',
                      new_callable=MagicMock) as mock_do_show_dataset_details_by_row_index:
        # Connect the action
        show_dataset_action.connect("activate", main_window.do_show_dataset_details_by_row_index)

        # Trigger the action
        show_dataset_action.activate(row_index_variant)

        # Assert that do_show_dataset_details_by_row_index was called once
        mock_do_show_dataset_details_by_row_index.assert_called_once_with(show_dataset_action, row_index_variant)


@pytest.mark.asyncio
async def test_do_search_select_and_show_direct_call(populated_app_with_mock_data, mock_get_datasets):
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

    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Create a GLib.Variant with the test search query
    mock_variant = GLib.Variant.new_string("test_search_query")

    # Call the method with the test search query
    main_window.do_search_select_and_show(None, mock_variant)

    # Assertions to check the state of the application after the search
    assert len(main_window.dataset_list_box.get_children()) > 0, "No datasets found in the list box"
    first_dataset_row = main_window.dataset_list_box.get_children()[0]
    dataset = first_dataset_row.dataset

    # Assert that the dataset's URI matches the expected URI
    assert dataset.uri == mock_get_datasets[0]['uri'], f"Expected URI {mock_get_datasets[0]['uri']}, got {dataset.uri}"

    # Await completion of all tasks related to the test
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)


@pytest.mark.asyncio
async def test_do_search_select_and_show_action_trigger(running_app):
    """Test if 'search-select-show' action triggers do_search_select_and_show method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Mock dependencies
    # mock_base_uri_list_box = MagicMock()
    # main_window.base_uri_list_box = mock_base_uri_list_box

    # Setup necessary mocks for the action trigger
    main_window._search_select_and_show = MagicMock()

    # Create and add the action
    search_variant = GLib.Variant.new_string("test_search_query")
    search_select_show_action = Gio.SimpleAction.new("search-select-show", search_variant.get_type())
    main_window.add_action(search_select_show_action)

    # Patch do_search_select_and_show method after action is added
    with patch.object(main_window, 'do_search_select_and_show',
                      new_callable=MagicMock) as mock_do_search_select_and_show:
        # Connect the action
        search_select_show_action.connect("activate", main_window.do_search_select_and_show)

        # Trigger the action
        search_select_show_action.activate(search_variant)

        # Assert that do_search_select_and_show was called once
        mock_do_search_select_and_show.assert_called_once_with(search_select_show_action, search_variant)


@pytest.mark.asyncio
# @pytest.mark.skip(reason="no way of currently testing this")
async def test_do_get_item_direct_call(populated_app_with_local_dataset_data, local_dataset_uri, tmp_path):
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

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action to load datasets
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Select the first dataset
    # first_dataset_row = app_with_mock_dtool_lookup_api_calls_on_local_dataset.main_window.dataset_list_box.get_children()[0]
    # dataset = first_dataset_row.dataset

    # Assuming the first dataset's UUID as the item UUID (Replace this with the actual item UUID logic)

    def get_item_uuid(dataset, relpath):
        for identifier, properties in dataset.generate_manifest()["items"].items():
            if properties["relpath"] == relpath:
                return identifier
        return None

    dataset = dtoolcore.DataSet.from_uri(local_dataset_uri)
    print(dataset.generate_manifest())

    item_uuid = get_item_uuid(dataset, "tiny.png")
    main_window._get_selected_items = lambda: [('item_name', item_uuid)]

    # TODO: assert file size and file content agree with "tiny.png" in data folder

    # Define the destination file path
    dest_file = tmp_path / "destination_file"

    # Create a GLib.Variant with the destination file path
    dest_file_variant = GLib.Variant.new_string(str(dest_file))

    dest_file = tmp_path / "destination_file"
    print(f"Destination file path: {dest_file}")

    # Call the do_get_item method without 'await'
    try:
        main_window.do_get_item(None, dest_file_variant)
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

    # Assert File Size
    original_file = Path('test/data/tiny.png')  # Path to the original file
    assert dest_file.stat().st_size == original_file.stat().st_size, "Downloaded file size does not match the original file size"

    # Assert File Content
    with open(dest_file, 'rb') as f_downloaded, open(original_file, 'rb') as f_original:
        assert f_downloaded.read() == f_original.read(), "Downloaded file content does not match the original file content"

    # Assert Modification Time
    current_time = time.time()
    assert dest_file.stat().st_mtime <= current_time, "Downloaded file modification time is in the future"

    # Optional: Assert File Permissions

@pytest.mark.asyncio
async def test_do_get_item_action_trigger(running_app):
    """Test if 'get-item' action triggers do_get_item method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Mock dependencies
    mock_dataset_list_box = MagicMock()
    main_window.dataset_list_box = mock_dataset_list_box
    mock_settings = MagicMock()
    main_window.settings = mock_settings

    # Setup necessary mocks for the action trigger
    mock_dataset = MagicMock()
    mock_dataset.get_item = AsyncMock()
    mock_dataset_list_box.get_selected_row.return_value = MagicMock(dataset=mock_dataset)
    main_window._get_selected_items = MagicMock(return_value=[('item_name', 'item_uuid')])

    # Create and add the action
    dest_file_variant = GLib.Variant.new_string("dummy_path")
    get_item_action = Gio.SimpleAction.new("get-item", dest_file_variant.get_type())
    main_window.add_action(get_item_action)

    # Patch do_get_item method after action is added
    with patch.object(main_window, 'do_get_item', new_callable=MagicMock) as mock_do_get_item:
        # Connect the action
        get_item_action.connect("activate", main_window.do_get_item)

        # Trigger the action
        get_item_action.activate(dest_file_variant)

        # Assert that do_get_item was called once
        mock_do_get_item.assert_called_once_with(get_item_action, dest_file_variant)


@pytest.mark.asyncio
async def test_do_refresh_view_direct_call(running_app):
    """Test the direct call of the do_refresh_view method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Directly call the do_refresh_view method
    main_window.do_refresh_view(None, None)


@pytest.mark.asyncio
async def test_refresh_method_triggered_by_action(running_app):
    """Test if the 'refresh-view' action triggers the refresh method."""

    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Patch the main window's refresh method
    with patch.object(main_window, 'refresh', new_callable=MagicMock) as mock_refresh:
        # Trigger the 'refresh-view' action
        main_window.activate_action('refresh-view')

        # Assert that the refresh method was called once
        mock_refresh.assert_called_once()

# tests for the do_put_annotation action and put-tag action

@pytest.mark.asyncio
async def test_do_put_annotation_direct_call(populated_app_with_local_dataset_data):
    """
    Test the do_put_annotation method for adding an annotation.
    It verifies if the annotation is correctly added to the selected dataset.
    """
    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)
        return False  # Timeout reached

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action to load datasets
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Select the first dataset
    main_window.activate_action('select-dataset', GLib.Variant.new_uint32(0))

    # Define annotation key and value
    annotation_key = "test_annotation_key"
    annotation_value = "test_annotation_value"
    annotation_variant = GLib.Variant.new_tuple(GLib.Variant.new_string(annotation_key), GLib.Variant.new_string(annotation_value))

    # Call the do_put_annotation method
    main_window.do_put_annotation(None, annotation_variant)

    # Retrieve the selected dataset to verify the annotation
    selected_row = main_window.dataset_list_box.get_selected_row()
    assert selected_row is not None, "No dataset is selected"
    selected_dataset = selected_row.dataset

     # Retrieve all annotations
    annotations = await selected_dataset.get_annotations()

    # Verify that the new annotation is present
    assert (annotation_key, annotation_value) in annotations.items(), (
        f"Expected annotation ({annotation_key}: {annotation_value}) not found in the dataset"
    )



@pytest.mark.asyncio
async def test_do_put_annotation_action_trigger(running_app):
    """Test if the 'put-annotation' action triggers the do_put_annotation method."""
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    with patch.object(main_window, '_put_annotation', new_callable=MagicMock) as mock_put_annotation:
        action = main_window.lookup_action("put-annotation")
        action.activate(GLib.Variant.new_tuple(GLib.Variant.new_string("key"), GLib.Variant.new_string("value")))
        mock_put_annotation.assert_called_once_with("key", "value")
        

@pytest.mark.asyncio
async def test_do_put_tag_direct_call(populated_app_with_local_dataset_data):
    """
    Test the do_put_tag method for adding a tag.
    It verifies if the tag is correctly added to the selected dataset.
    """
    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True  # Datasets are loaded
            await asyncio.sleep(0.1)
        return False  # Timeout reached

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action to load datasets
    main_window.activate_action('refresh-view')

    # Wait until datasets are loaded
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Select the first dataset
    main_window.activate_action('select-dataset', GLib.Variant.new_uint32(0))

    # Define the tag
    tag_value = "test_tag"
    tag_variant = GLib.Variant.new_string(tag_value)

    # Call the do_put_tag method
    main_window.do_put_tag(None, tag_variant)

    # Retrieve the selected dataset to verify the tag
    selected_row = main_window.dataset_list_box.get_selected_row()
    assert selected_row is not None, "No dataset is selected"
    selected_dataset = selected_row.dataset

    assert tag_value in await selected_dataset.get_tags(), f"Expected tag '{tag_value}' not found in the dataset"

@pytest.mark.asyncio
async def test_do_put_tag_action_trigger(running_app):
    """Test if the 'put-tag' action triggers the do_put_tag method."""
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    with patch.object(main_window, '_put_tag', new_callable=MagicMock) as mock_put_tag:
        action = main_window.lookup_action("put-tag")
        action.activate(GLib.Variant.new_string("tag"))
        mock_put_tag.assert_called_once_with("tag")


@pytest.mark.asyncio
async def test_do_select_dataset_row_by_uri_direct_call(populated_app_with_mock_data):
    """
    Test the do_select_dataset_row_by_uri method for directly selecting a dataset row by URI.
    It verifies if the dataset list is correctly populated and the specified dataset row is selected.
    """

    async def wait_for_datasets_to_load(list_box, timeout=10):
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if len(list_box.get_children()) > 0:
                return True
            await asyncio.sleep(0.1)
        return False

    windows = populated_app_with_mock_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Trigger the 'refresh-view' action and wait for datasets to load
    main_window.activate_action('refresh-view')
    datasets_loaded = await wait_for_datasets_to_load(main_window.dataset_list_box)
    assert datasets_loaded, "Datasets were not loaded in time"

    # Define a URI that corresponds to a dataset in the populated dataset list
    test_uri = "s3://test-bucket/1a1f9fad-8589-413e-9602-5bbd66bfe675"

    # Create a GLib.Variant with the test URI
    uri_variant = GLib.Variant.new_string(test_uri)

    dummy_action = Gio.SimpleAction.new("select-dataset-by-uri", uri_variant.get_type())

    # Call the do_select_dataset_row_by_uri method with the test URI
    main_window.do_select_dataset_row_by_uri(dummy_action , uri_variant)

    # Retrieve the dataset that should be selected based on the URI
    index = main_window.dataset_list_box.get_row_index_from_uri(test_uri)
    selected_row = main_window.dataset_list_box.get_row_at_index(index)
    selected_dataset = selected_row.dataset if selected_row is not None else None

    # Assert that the dataset with the given URI is selected
    assert selected_dataset is not None, "No dataset was selected"
    assert selected_dataset.uri == test_uri, f"Expected URI {test_uri}, got {selected_dataset.uri}"

    # Await completion of all tasks related to the test
    pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending_tasks:
        await asyncio.gather(*pending_tasks)



# ---------------------------------------------------------------------------
# Tests for base URI listing timeout — fixes #45
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="activate_action('refresh-view') alone does not select a base-URI row "
                          "in this fixture, so the listing path (and its asyncio.wait_for timeout) "
                          "is never reached and no timeout error is logged. Needs explicit "
                          "base-URI row selection to exercise the #45 timeout feature.",
                   strict=False)
@pytest.mark.asyncio
async def test_base_uri_listing_timeout_shows_error(populated_app_with_local_dataset_data,
                                                     local_dataset_uri, caplog):
    """When all_datasets() takes longer than the timeout, an error is logged
    and the row info label is updated — the spinner must not hang forever.
    """
    import asyncio as _asyncio
    from unittest.mock import patch, AsyncMock
    from dtool_lookup_gui.views.main_window import MainWindow
    from dtool_lookup_gui.models.settings import settings

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Set a very short timeout so the test runs fast
    original_timeout = settings.base_uri_listing_timeout
    settings.base_uri_listing_timeout = 1  # 1 second

    async def slow_all_datasets():
        await _asyncio.sleep(10)  # Much longer than the timeout
        return []

    try:
        with patch(
            "dtool_lookup_gui.models.base_uris.BaseURI.all_datasets",
            new=AsyncMock(side_effect=lambda: slow_all_datasets()),
        ):
            with caplog.at_level(logging.ERROR, logger="dtool_lookup_gui.views.main_window"):
                main_window.activate_action("refresh-view")
                # Wait long enough for timeout to fire (timeout=1s + some margin)
                await _asyncio.sleep(2.5)

        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert error_records, "Expected a timeout error to be logged"
        msg = error_records[-1].message
        assert "timed out" in msg.lower() or "timeout" in msg.lower(), \
            f"Expected timeout message, got: {msg!r}"
    finally:
        settings.base_uri_listing_timeout = original_timeout


@pytest.mark.xfail(reason="activate_action('refresh-view') alone does not select a base-URI row "
                          "in this fixture, so BaseURI.all_datasets() is never reached and the "
                          "patched listing never runs. Needs explicit base-URI row selection to "
                          "exercise the timeout-disabled path; tracked with the #45 timeout work.",
                   strict=False)
@pytest.mark.asyncio
async def test_base_uri_listing_no_timeout_when_disabled(populated_app_with_local_dataset_data,
                                                          local_dataset_uri, caplog):
    """When timeout is set to 0, slow listings must NOT raise TimeoutError."""
    import asyncio as _asyncio
    from unittest.mock import patch, AsyncMock
    from dtool_lookup_gui.views.main_window import MainWindow
    from dtool_lookup_gui.models.settings import settings

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    original_timeout = settings.base_uri_listing_timeout
    settings.base_uri_listing_timeout = 0  # disabled

    call_completed = []

    async def slow_but_completes():
        await _asyncio.sleep(0.5)
        call_completed.append(True)
        return []

    try:
        # Pass the coroutine function directly so AsyncMock awaits it; a
        # lambda returning slow_but_completes() would yield an un-awaited
        # coroutine and the body would never run.
        with patch(
            "dtool_lookup_gui.models.base_uris.BaseURI.all_datasets",
            new=AsyncMock(side_effect=slow_but_completes),
        ):
            main_window.activate_action("refresh-view")
            await _asyncio.sleep(2.0)

        timeout_errors = [r for r in caplog.records
                          if r.levelno >= logging.ERROR and "timeout" in r.message.lower()]
        assert not timeout_errors, \
            "No timeout errors expected when timeout is disabled (0)"
        assert call_completed, "all_datasets() should have completed normally"
    finally:
        settings.base_uri_listing_timeout = original_timeout


# ---------------------------------------------------------------------------
# Tests for README tree rebuild after save — fixes #526
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="do_save_metadata / on_save_metadata_button_clicked calls "
                          "MainWindow._rebuild_readme_tree which does not exist, so the tree is "
                          "never rebuilt after save. See issue #526.",
                   strict=False)
@pytest.mark.asyncio
async def test_readme_tree_rebuilt_after_save(populated_app_with_local_dataset_data,
                                               local_dataset_uri):
    """After saving README metadata, the tree view must reflect the new content
    without requiring dataset re-selection.
    """
    import asyncio as _asyncio
    import time
    import yaml
    from unittest.mock import patch, MagicMock
    from dtool_lookup_gui.views.main_window import MainWindow

    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Load a dataset so there's a selection
    main_window.activate_action("refresh-view")
    start = time.time()
    while time.time() - start < 10:
        if len(main_window.dataset_list_box.get_children()) > 0:
            break
        await _asyncio.sleep(0.1)

    rows = main_window.dataset_list_box.get_children()
    assert rows, "Need at least one dataset row to test README save"
    main_window.dataset_list_box.select_row(rows[0])
    await _asyncio.sleep(1.0)  # Let _update_dataset_view run

    new_readme = "project: test-project\nauthor: Test Author\nversion: 42\n"

    # Patch put_readme so we don't write to disk
    with patch.object(rows[0].dataset, "put_readme", return_value=None):
        main_window.readme_buffer.set_text(new_readme)

        # Simulate save button click (linting off path or linting pass path)
        with patch("dtool_lookup_gui.models.settings.settings.yaml_linting_enabled", False):
            main_window.on_save_metadata_button_clicked(None)

    # Give GTK a moment to process
    await _asyncio.sleep(0.2)

    # The tree store must now contain entries matching the new YAML
    store = main_window.readme_tree_view.get_model()
    assert store is not None, "Tree view must have a model"

    tree_keys = set()
    def collect_keys(model, path, iter_):
        tree_keys.add(model[iter_][0])
    store.foreach(collect_keys)

    expected_keys = {"project", "author", "version"}
    assert expected_keys.issubset(tree_keys), \
        f"Tree must contain keys from new README. Expected {expected_keys}, found {tree_keys}"
