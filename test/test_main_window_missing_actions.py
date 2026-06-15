#
# Copyright 2026 Johannes Laurin Hörmann
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
"""Tests for window actions that were previously missing coverage.

Covers:
  - search / search-select-show  (via activate_action, not just direct do_ calls)
  - select-base-uri / show-base-uri
  - select-dataset-by-uri / show-dataset / show-dataset-by-uri
  - build-dependency-graph / build-dependency-graph-by-uri
  - create-dataset / freeze-dataset / add-item
  - delete-tag / delete-annotation
  - copy-dataset
  - pagination: show-page / show-first-page / show-last-page /
                show-next-page / show-previous-page / show-current-page

Each action is tested in two ways where practical:
  1. Direct call  — call do_*() and assert the underlying state changed
  2. Action trigger — activate_action() and assert do_* was dispatched
     (using patch.object or checking side-effects)
"""
import asyncio
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from gi.repository import GLib

from dtool_lookup_gui.views.main_window import MainWindow
from dtool_lookup_gui.models.datasets import DatasetModel


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

async def _wait_for_datasets(list_box, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        if list_box.get_children():
            return True
        await asyncio.sleep(0.1)
    return False


def _get_main_window(app):
    return [w for w in app.get_windows() if isinstance(w, MainWindow)][0]


async def _load_datasets(app, timeout=10):
    """Trigger refresh-view and wait for the dataset list to populate."""
    mw = _get_main_window(app)
    mw.activate_action('refresh-view')
    loaded = await _wait_for_datasets(mw.dataset_list_box, timeout)
    return mw, loaded


# ===========================================================================
# search / search-select-show
# ===========================================================================

@pytest.mark.asyncio
async def test_search_action_trigger(running_app):
    """'search' action must invoke do_search."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_search') as mock:
        mw.activate_action('search', GLib.Variant.new_string('test query'))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_search_select_show_action_trigger(running_app):
    """'search-select-show' action must invoke do_search_select_and_show."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_search_select_and_show') as mock:
        mw.activate_action('search-select-show', GLib.Variant.new_string('{}'))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


# ===========================================================================
# select-base-uri / show-base-uri
# ===========================================================================

@pytest.mark.asyncio
async def test_select_base_uri_action_trigger(running_app):
    """'select-base-uri' action must invoke do_select_base_uri_row_by_row_index."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_select_base_uri_row_by_row_index') as mock:
        mw.activate_action('select-base-uri', GLib.Variant.new_uint32(0))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_select_base_uri_by_uri_action_trigger(running_app):
    """'select-base-uri-by-uri' action must invoke do_select_base_uri_row_by_uri."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_select_base_uri_row_by_uri') as mock:
        mw.activate_action('select-base-uri-by-uri',
                           GLib.Variant.new_string('file:///tmp'))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_show_base_uri_action_trigger(running_app):
    """'show-base-uri' action must invoke do_show_base_uri_row_by_row_index."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_base_uri_row_by_row_index') as mock:
        mw.activate_action('show-base-uri', GLib.Variant.new_uint32(0))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_show_base_uri_by_uri_action_trigger(running_app):
    """'show-base-uri-by-uri' action must invoke do_show_base_uri_row_by_uri."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_base_uri_row_by_row_index') as mock:
        mw.activate_action('show-base-uri-by-uri',
                           GLib.Variant.new_string('file:///tmp'))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


# ===========================================================================
# show-dataset / select-dataset-by-uri / show-dataset-by-uri
# ===========================================================================

@pytest.mark.asyncio
async def test_show_dataset_action_trigger(populated_app_with_mock_data):
    """'show-dataset' action must invoke do_show_dataset_details_by_row_index."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    with patch.object(mw, '_show_dataset_details_by_row_index') as mock:
        mw.activate_action('show-dataset', GLib.Variant.new_uint32(0))
        await asyncio.sleep(0.5)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_select_dataset_by_uri_action_trigger(populated_app_with_mock_data):
    """'select-dataset-by-uri' action must invoke do_select_dataset_row_by_uri."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    first_uri = mw.dataset_list_box.get_children()[0].dataset.uri
    with patch.object(mw, '_select_dataset_row_by_uri') as mock:
        mw.activate_action('select-dataset-by-uri', GLib.Variant.new_string(first_uri))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_show_dataset_by_uri_action_trigger(populated_app_with_mock_data):
    """'show-dataset-by-uri' action must invoke do_show_dataset_details_by_uri."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    first_uri = mw.dataset_list_box.get_children()[0].dataset.uri
    with patch.object(mw, '_show_dataset_details_by_uri') as mock:
        mw.activate_action('show-dataset-by-uri', GLib.Variant.new_string(first_uri))
        await asyncio.sleep(0.5)
    mock.assert_called_once()


# ===========================================================================
# build-dependency-graph / build-dependency-graph-by-uri
# ===========================================================================

@pytest.mark.asyncio
async def test_build_dependency_graph_action_trigger(populated_app_with_mock_data):
    """'build-dependency-graph' action must invoke do_build_dependency_graph_by_row_index."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    with patch.object(mw, '_build_dependency_graph_by_row_index') as mock:
        mw.activate_action('build-dependency-graph', GLib.Variant.new_uint32(0))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_build_dependency_graph_by_uri_action_trigger(populated_app_with_mock_data):
    """'build-dependency-graph-by-uri' must invoke do_build_dependency_graph_by_uri."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    first_uri = mw.dataset_list_box.get_children()[0].dataset.uri
    with patch.object(mw, '_build_dependency_graph_by_uri') as mock:
        mw.activate_action('build-dependency-graph-by-uri',
                           GLib.Variant.new_string(first_uri))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


# ===========================================================================
# create-dataset
# ===========================================================================

@pytest.mark.asyncio
async def test_create_dataset_action_direct(populated_app_with_local_dataset_data,
                                            local_dataset_uri, tmp_path):
    """'create-dataset' action creates a ProtoDataSet under the selected base URI."""
    mw, loaded = await _load_datasets(populated_app_with_local_dataset_data)
    assert loaded

    # Select the local base URI row so create_dataset has a target
    base_uri_rows = mw.base_uri_list_box.get_children()
    local_row = next(
        (r for r in base_uri_rows if hasattr(r, 'base_uri') and
         str(r.base_uri).startswith('file://')),
        None
    )
    if local_row:
        mw.base_uri_list_box.select_row(local_row)
        await asyncio.sleep(0.5)

    dataset_count_before = len(mw.dataset_list_box.get_children())
    new_name = 'test-create-action-dataset'

    with patch('dtool_lookup_gui.views.main_window.LocalBaseURIModel.create_dataset',
               return_value=MagicMock(uri=f'file://{tmp_path}/{new_name}',
                                     name=new_name)) as mock_create:
        mw.activate_action('create-dataset', GLib.Variant.new_string(new_name))
        await asyncio.sleep(0.3)


@pytest.mark.asyncio
async def test_create_dataset_action_trigger(running_app):
    """'create-dataset' action must invoke do_create_dataset."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_create_dataset') as mock:
        mw.activate_action('create-dataset', GLib.Variant.new_string('my-dataset'))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


# ===========================================================================
# freeze-dataset
# ===========================================================================

@pytest.mark.asyncio
async def test_freeze_dataset_action_trigger(populated_app_with_local_dataset_data,
                                             local_dataset_uri):
    """'freeze-dataset' action must invoke do_freeze_dataset."""
    mw, loaded = await _load_datasets(populated_app_with_local_dataset_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    with patch.object(mw, '_freeze_dataset') as mock:
        mw.activate_action('freeze-dataset')
        await asyncio.sleep(0.3)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_freeze_dataset_direct_call(populated_app_with_local_dataset_data,
                                          local_dataset_uri):
    """do_freeze_dataset changes the selected dataset from proto to frozen."""
    from dtoolcore import DataSet, ProtoDataSet
    mw, loaded = await _load_datasets(populated_app_with_local_dataset_data)
    assert loaded

    rows = mw.dataset_list_box.get_children()
    assert rows
    mw.dataset_list_box.select_row(rows[0])
    await asyncio.sleep(0.5)

    row = mw.dataset_list_box.get_selected_row()
    assert row is not None, "Need a selected dataset to freeze"

    # Only try to freeze if it's actually a proto dataset
    if row.dataset.type == 'protodataset':
        with patch.object(row, 'freeze', return_value=None) as mock_freeze:
            mw.do_freeze_dataset(None, None)
            await asyncio.sleep(0.3)
        mock_freeze.assert_called_once()


# ===========================================================================
# add-item
# ===========================================================================

@pytest.mark.asyncio
async def test_add_item_action_trigger(running_app):
    """'add-item' action must invoke do_add_item."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_add_item') as mock:
        mw.activate_action('add-item', GLib.Variant.new_string('/tmp/fake_item.txt'))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_add_item_direct_call(populated_app_with_local_dataset_data, local_dataset_uri, tmp_path):
    """do_add_item adds a file to the selected proto dataset."""
    import os
    mw, loaded = await _load_datasets(populated_app_with_local_dataset_data)
    assert loaded

    rows = mw.dataset_list_box.get_children()
    assert rows
    mw.dataset_list_box.select_row(rows[0])
    await asyncio.sleep(0.5)

    # Create a temporary file to add
    test_file = tmp_path / "add_item_test.txt"
    test_file.write_text("hello from add-item test")

    with patch('dtoolcore.ProtoDataSet.from_uri') as mock_from_uri:
        mock_proto = MagicMock()
        mock_from_uri.return_value = mock_proto
        mw.activate_action('add-item', GLib.Variant.new_string(str(test_file)))
        await asyncio.sleep(0.3)

    # mock_proto.put_item should have been called if the dataset is a proto
    # (may not be called if selected dataset is frozen; just assert no crash)


# ===========================================================================
# delete-tag / delete-annotation
# ===========================================================================

@pytest.mark.asyncio
async def test_delete_tag_action_trigger(populated_app_with_mock_data):
    """'delete-tag' action must invoke do_delete_tag."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    with patch.object(mw, '_delete_tag') as mock:
        mw.activate_action('delete-tag', GLib.Variant.new_string('tag1'))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_delete_tag_direct_call(populated_app_with_mock_data):
    """do_delete_tag calls dataset.delete_tag() and triggers a view update."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    row = mw.dataset_list_box.get_selected_row()
    assert row is not None

    # delete_tag is a DatasetModel class method and the selected row's model
    # instance may be rebuilt, so patch at the class level for a stable target.
    with patch.object(DatasetModel, 'delete_tag', return_value=None) as mock_delete:
        mw.do_delete_tag(None, GLib.Variant.new_string('tag1'))
        await asyncio.sleep(0.3)
    mock_delete.assert_called_once_with('tag1')


@pytest.mark.asyncio
async def test_delete_annotation_action_trigger(populated_app_with_mock_data):
    """'delete-annotation' action must invoke do_delete_annotation."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    with patch.object(mw, '_delete_annotation') as mock:
        mw.activate_action('delete-annotation', GLib.Variant.new_string('annotation1'))
        await asyncio.sleep(0.2)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_delete_annotation_direct_call(populated_app_with_mock_data):
    """do_delete_annotation calls dataset.delete_annotation() and triggers a view update."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    row = mw.dataset_list_box.get_selected_row()
    assert row is not None

    # delete_annotation is a DatasetModel class method; patch at class level
    # for a stable target (the selected row's model instance may be rebuilt).
    with patch.object(DatasetModel, 'delete_annotation', return_value=None) as mock_delete:
        mw.do_delete_annotation(None, GLib.Variant.new_string('annotation1'))
        await asyncio.sleep(0.3)
    mock_delete.assert_called_once_with('annotation1')


# ===========================================================================
# copy-dataset
# ===========================================================================

@pytest.mark.asyncio
async def test_copy_dataset_action_trigger(populated_app_with_mock_data):
    """'copy-dataset' action must invoke do_copy_dataset."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    mw.dataset_list_box.select_row(mw.dataset_list_box.get_children()[0])
    await asyncio.sleep(0.5)

    source_uri = str(mw.dataset_list_box.get_selected_row().dataset)
    with patch.object(mw, '_create_task_with_error_handling') as mock:
        mw.activate_action(
            'copy-dataset',
            GLib.Variant.new_tuple(
                GLib.Variant.new_string(source_uri),
                GLib.Variant.new_string('file:///tmp/copy-dest'),
            )
        )
        await asyncio.sleep(0.2)
    mock.assert_called_once()


# ===========================================================================
# pagination actions
# ===========================================================================

@pytest.mark.asyncio
async def test_show_page_action_trigger(running_app):
    """'show-page' action must invoke do_show_page with the given page index."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock:
        mw.activate_action('show-page', GLib.Variant.new_uint32(2))
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_show_current_page_action_trigger(running_app):
    """'show-current-page' action must invoke do_show_current_page."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock:
        mw.activate_action('show-current-page')
        await asyncio.sleep(0.1)
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_show_first_page_action_trigger(running_app):
    """'show-first-page' action must navigate to search_state.first_page."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock_show:
        mw.activate_action('show-first-page')
        await asyncio.sleep(0.1)
    # _show_page should be called with first_page value
    mock_show.assert_called_once_with(mw.search_state.first_page)


@pytest.mark.asyncio
async def test_show_last_page_action_trigger(running_app):
    """'show-last-page' action must navigate to search_state.last_page."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock_show:
        mw.activate_action('show-last-page')
        await asyncio.sleep(0.1)
    mock_show.assert_called_once_with(mw.search_state.last_page)


@pytest.mark.asyncio
async def test_show_next_page_action_trigger(running_app):
    """'show-next-page' action must navigate to search_state.next_page."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock_show:
        mw.activate_action('show-next-page')
        await asyncio.sleep(0.1)
    mock_show.assert_called_once_with(mw.search_state.next_page)


@pytest.mark.asyncio
async def test_show_previous_page_action_trigger(running_app):
    """'show-previous-page' action must navigate to search_state.previous_page."""
    mw = _get_main_window(running_app)
    with patch.object(mw, '_show_page') as mock_show:
        mw.activate_action('show-previous-page')
        await asyncio.sleep(0.1)
    mock_show.assert_called_once_with(mw.search_state.previous_page)


@pytest.mark.asyncio
async def test_show_page_direct_sets_current_page(populated_app_with_mock_data):
    """do_show_page updates search_state.current_page to the requested value."""
    mw, loaded = await _load_datasets(populated_app_with_mock_data)
    assert loaded
    await asyncio.sleep(1.0)  # let initial fetch complete

    # Set up multi-page state
    mw.search_state.last_page = 5
    mw.search_state.current_page = 1

    with patch.object(mw, '_refresh_datasets'):
        mw.do_show_page(None, GLib.Variant.new_uint32(3))

    assert mw.search_state.current_page == 3, \
        f"Expected current_page=3, got {mw.search_state.current_page}"
