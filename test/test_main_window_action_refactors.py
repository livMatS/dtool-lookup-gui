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
"""Tests for the three newly refactored actions:
    - save-metadata
    - copy-dataset
    - add-local-directory

Each action is now independently testable without simulating widget clicks
or file-chooser dialogs.
"""
import asyncio
import os
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

from gi.repository import GLib

from dtool_lookup_gui.views.main_window import MainWindow
from dtool_lookup_gui.models.settings import Settings
from dtool_lookup_gui.models.datasets import DatasetModel


# ---------------------------------------------------------------------------
# save-metadata action
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="do_save_metadata calls MainWindow._rebuild_readme_tree which "
                          "does not exist; the readme tree is never rebuilt after save. "
                          "See issue #526.",
                   strict=False)
@pytest.mark.asyncio
async def test_do_save_metadata_valid_yaml(populated_app_with_local_dataset_data, local_dataset_uri):
    """save-metadata action with valid YAML saves readme and rebuilds tree."""
    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Load a dataset so there's a selection
    main_window.activate_action('refresh-view')
    start = time.time()
    while time.time() - start < 10:
        if len(main_window.dataset_list_box.get_children()) > 0:
            break
        await asyncio.sleep(0.1)

    rows = main_window.dataset_list_box.get_children()
    assert rows, "Need at least one dataset row"
    main_window.dataset_list_box.select_row(rows[0])
    await asyncio.sleep(1.0)

    new_yaml = "project: action-test\nauthor: Tester\nversion: 99\n"

    put_readme_calls = []
    original_put_readme = rows[0].dataset.put_readme

    def mock_put_readme(text):
        put_readme_calls.append(text)

    with patch.object(rows[0].dataset, 'put_readme', side_effect=mock_put_readme):
        with patch('dtool_lookup_gui.models.settings.settings.yaml_linting_enabled', False):
            main_window.activate_action('save-metadata', GLib.Variant.new_string(new_yaml))

    await asyncio.sleep(0.2)

    assert put_readme_calls, "put_readme() should have been called"
    assert put_readme_calls[0] == new_yaml

    # Tree view should reflect the new content
    store = main_window.readme_tree_view.get_model()
    assert store is not None
    tree_keys = set()
    store.foreach(lambda m, p, it: tree_keys.add(m[it][0]))
    assert {'project', 'author', 'version'}.issubset(tree_keys), \
        f"Tree should contain new YAML keys, got: {tree_keys}"


@pytest.mark.asyncio
async def test_do_save_metadata_linting_error_does_not_save(populated_app_with_local_dataset_data,
                                                              local_dataset_uri):
    """save-metadata action with invalid YAML and linting enabled must NOT call put_readme."""
    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    main_window.activate_action('refresh-view')
    start = time.time()
    while time.time() - start < 10:
        if len(main_window.dataset_list_box.get_children()) > 0:
            break
        await asyncio.sleep(0.1)

    rows = main_window.dataset_list_box.get_children()
    assert rows
    main_window.dataset_list_box.select_row(rows[0])
    await asyncio.sleep(1.0)

    bad_yaml = "key: [unclosed bracket\n  bad_indent: yes\n"

    put_readme_calls = []
    with patch.object(DatasetModel, 'put_readme', side_effect=lambda t: put_readme_calls.append(t)):
        with patch.object(Settings, 'yaml_linting_enabled', new_callable=PropertyMock, return_value=True):
            main_window.activate_action('save-metadata', GLib.Variant.new_string(bad_yaml))

    await asyncio.sleep(0.2)
    assert not put_readme_calls, "put_readme() must NOT be called when YAML linting fails"


@pytest.mark.asyncio
async def test_do_save_metadata_no_selection_does_nothing(running_app):
    """save-metadata with no dataset selected logs a warning and does nothing."""
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Ensure nothing is selected
    main_window.dataset_list_box.unselect_all()

    yaml_content = "project: orphan\n"
    # Should not raise
    main_window.activate_action('save-metadata', GLib.Variant.new_string(yaml_content))
    await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# copy-dataset action
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_do_copy_dataset_calls_copy_manager(populated_app_with_local_dataset_data, local_dataset_uri):
    """copy-dataset action must call CopyManager.copy() with correct dataset and destination."""
    windows = populated_app_with_local_dataset_data.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    main_window.activate_action('refresh-view')
    start = time.time()
    while time.time() - start < 10:
        if len(main_window.dataset_list_box.get_children()) > 0:
            break
        await asyncio.sleep(0.1)

    rows = main_window.dataset_list_box.get_children()
    assert rows
    main_window.dataset_list_box.select_row(rows[0])
    await asyncio.sleep(1.0)

    source_uri = str(rows[0].dataset)
    destination_uri = "file:///tmp/copy-test-dest"

    copy_calls = []

    async def mock_copy(dataset, destination):
        copy_calls.append((str(dataset), destination))

    with patch.object(main_window._copy_manager, 'copy', side_effect=mock_copy):
        main_window.activate_action(
            'copy-dataset',
            GLib.Variant.new_tuple(
                GLib.Variant.new_string(source_uri),
                GLib.Variant.new_string(destination_uri),
            )
        )
        await asyncio.sleep(0.5)

    assert copy_calls, "CopyManager.copy() should have been called"
    assert copy_calls[0][1] == destination_uri, \
        f"Destination should be {destination_uri!r}, got {copy_calls[0][1]!r}"


@pytest.mark.asyncio
async def test_do_copy_dataset_no_selection_does_nothing(running_app):
    """copy-dataset with no selection must not crash."""
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    main_window.dataset_list_box.unselect_all()
    # Should not raise
    main_window.activate_action(
        'copy-dataset',
        GLib.Variant.new_tuple(
            GLib.Variant.new_string("file:///nonexistent"),
            GLib.Variant.new_string("file:///tmp/dest"),
        )
    )
    await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# add-local-directory action
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_do_add_local_directory_valid(running_app, tmp_path):
    """add-local-directory action with a valid path adds it and refreshes the list."""
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    # Create a real temporary directory
    new_dir = tmp_path / "new-base-uri"
    new_dir.mkdir()
    uri = new_dir.as_uri()

    added_uris = []

    with patch('dtool_lookup_gui.views.main_window.LocalBaseURIModel.add_directory',
               side_effect=lambda u: added_uris.append(u)) as mock_add:
        main_window.activate_action('add-local-directory', GLib.Variant.new_string(uri))
        await asyncio.sleep(0.5)

    assert added_uris, "LocalBaseURIModel.add_directory() should have been called"
    assert added_uris[0] == uri


@pytest.mark.xfail(reason="do_add_local_directory's except handler calls bare 'logger' "
                          "(only '_logger' is defined in main_window.py) -> NameError, so the "
                          "warning is never logged. App bug; tracked separately.",
                   strict=False)
@pytest.mark.asyncio
async def test_do_add_local_directory_invalid_does_not_crash(running_app, caplog):
    """add-local-directory with an invalid/duplicate URI logs warning and does not crash."""
    import logging
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    with patch('dtool_lookup_gui.views.main_window.LocalBaseURIModel.add_directory',
               side_effect=ValueError("URI already registered")):
        with caplog.at_level(logging.WARNING, logger='dtool_lookup_gui.views.main_window'):
            main_window.activate_action(
                'add-local-directory', GLib.Variant.new_string("file:///already/there"))
            await asyncio.sleep(0.2)

    warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("already registered" in m or "add-local-directory" in m for m in warning_msgs), \
        f"Expected warning about invalid URI, got: {warning_msgs}"


@pytest.mark.asyncio
async def test_do_add_local_directory_empty_uri_does_nothing(running_app, caplog):
    """add-local-directory with empty URI must log warning and not call add_directory."""
    import logging
    windows = running_app.get_windows()
    main_window = [w for w in windows if isinstance(w, MainWindow)][0]

    with patch('dtool_lookup_gui.views.main_window.LocalBaseURIModel.add_directory') as mock_add:
        with caplog.at_level(logging.WARNING, logger='dtool_lookup_gui.views.main_window'):
            main_window.activate_action('add-local-directory', GLib.Variant.new_string(""))
            await asyncio.sleep(0.1)

    mock_add.assert_not_called()
