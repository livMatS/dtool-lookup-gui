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
"""Tests for the MainWindow menu / selection / search signal handlers.

These exercise the thin signal handlers against the real main window built
during app activation (via running_app), mocking the dialogs and actions they
delegate to. Assertions are grouped per handler family to limit the number of
(slow) app activations. The modal file-chooser handlers (open-local-directory,
add-items) use Gtk dialog.run() and are out of scope.
"""
from unittest.mock import MagicMock, patch

import pytest

from gi.repository import GLib, Gtk

from dtool_lookup_gui.views.main_window import MainWindow

_LAUNCH = "dtool_lookup_gui.views.main_window.launch_default_app_for_uri"


def _main_window(app):
    return [w for w in app.get_windows() if isinstance(w, MainWindow)][0]


@pytest.mark.asyncio
async def test_menu_handlers_show_their_windows(running_app):
    main_window = _main_window(running_app)
    handlers = [
        ("on_settings_clicked", "settings_dialog"),
        ("version_button_clicked", "server_versions_dialog"),
        ("config_button_clicked", "config_details"),
        ("on_logging_clicked", "log_window"),
        ("on_about_clicked", "about_dialog"),
    ]
    for handler_name, dialog_attr in handlers:
        with patch.object(getattr(main_window, dialog_attr), "show") as show:
            getattr(main_window, handler_name)(None)
        show.assert_called_once()


@pytest.mark.asyncio
async def test_on_create_dataset_clicked_opens_name_dialog(running_app):
    main_window = _main_window(running_app)
    with patch("dtool_lookup_gui.views.main_window.DatasetNameDialog") as dialog_cls:
        main_window.on_create_dataset_clicked(None)
    dialog_cls.assert_called_once()
    dialog_cls.return_value.show.assert_called_once()


@pytest.mark.asyncio
async def test_selection_and_search_handlers_activate_actions(running_app):
    main_window = _main_window(running_app)
    with patch.object(main_window, "activate_action") as activate:
        base_row = MagicMock()
        base_row.get_index.return_value = 2
        main_window.on_base_uri_selected(None, base_row)

        dataset_row = MagicMock()
        dataset_row.get_index.return_value = 5
        main_window.on_dataset_selected(None, dataset_row)

        main_window.search_entry.set_text("toluene")
        main_window.on_search_activate(None)

        # The None-row branches must be no-ops (no extra action activations).
        main_window.on_base_uri_selected(None, None)
        main_window.on_dataset_selected(None, None)

    activated = [call.args[0] for call in activate.call_args_list]
    assert activated == ["show-base-uri", "show-dataset", "search-select-show"]
    # The search action carries the entry text.
    search_call = next(c for c in activate.call_args_list
                       if c.args[0] == "search-select-show")
    assert search_call.args[1].get_string() == "toluene"


@pytest.mark.asyncio
async def test_refresh_dropdown_and_show_handlers(running_app):
    main_window = _main_window(running_app)

    # Refresh button delegates to the win-scoped refresh-view action.
    with patch.object(main_window, "get_action_group") as get_group:
        main_window.on_refresh_clicked(None)
        get_group.return_value.activate_action.assert_called_once_with(
            "refresh-view", None)

    # Drop-down toggles the search popover: visible -> popdown.
    with patch.object(main_window.search_popover, "get_visible", return_value=True), \
            patch.object(main_window.search_popover, "popdown") as popdown:
        main_window.on_search_drop_down_clicked(None)
        popdown.assert_called_once()

    # ... hidden -> popup_at the widget.
    with patch.object(main_window.search_popover, "get_visible", return_value=False), \
            patch.object(main_window.search_popover, "popup_at") as popup_at:
        widget = object()
        main_window.on_search_drop_down_clicked(widget)
        popup_at.assert_called_once_with(widget)


@pytest.mark.asyncio
async def test_on_show_clicked_launches_only_with_selection(running_app):
    main_window = _main_window(running_app)

    # No dataset selected -> warn and do nothing.
    with patch.object(main_window.dataset_list_box, "get_selected_row",
                      return_value=None), \
            patch(_LAUNCH) as launch:
        main_window.on_show_clicked(None)
        launch.assert_not_called()

    # A dataset selected -> launch the default app for its URI.
    row = MagicMock()
    row.dataset = "file:///some/dataset"
    with patch.object(main_window.dataset_list_box, "get_selected_row",
                      return_value=row), \
            patch(_LAUNCH) as launch:
        main_window.on_show_clicked(None)
        launch.assert_called_once_with("file:///some/dataset")


@pytest.mark.asyncio
async def test_pagination_buttons_activate_page_actions(running_app):
    main_window = _main_window(running_app)
    expected = [
        ("on_first_page_button_clicked", "show-first-page"),
        ("on_decrease_page_button_clicked", "show-previous-page"),
        ("on_previous_page_button_clicked", "show-previous-page"),
        ("on_current_page_button_clicked", "show-current-page"),
        ("on_next_page_button_clicked", "show-next-page"),
        ("on_increase_page_button_clicked", "show-next-page"),
        ("on_last_page_button_clicked", "show-last-page"),
    ]
    with patch.object(main_window, "activate_action") as activate:
        for handler_name, _ in expected:
            getattr(main_window, handler_name)(None)
    activated = [call.args[0] for call in activate.call_args_list]
    assert activated == [action for _, action in expected]


@pytest.mark.asyncio
async def test_on_readme_buffer_changed_enables_save_button(running_app):
    main_window = _main_window(running_app)
    main_window.save_metadata_button.set_sensitive(False)
    main_window.on_readme_buffer_changed(None)
    assert main_window.save_metadata_button.get_sensitive() is True


@pytest.mark.asyncio
async def test_manifest_row_activated_shows_dialog_for_single_item(running_app):
    main_window = _main_window(running_app)
    with patch.object(main_window, "_get_selected_items",
                      return_value=[("item.txt", "uuid-1")]), \
            patch.object(main_window, "_show_get_item_dialog") as show_dialog:
        main_window.on_manifest_row_activated(None, None, None)
    show_dialog.assert_called_once_with("item.txt", "uuid-1")


@pytest.mark.asyncio
async def test_manifest_row_activated_rejects_multiple_items(running_app):
    main_window = _main_window(running_app)
    with patch.object(main_window, "_get_selected_items", return_value=[]):
        with pytest.raises(ValueError):
            main_window.on_manifest_row_activated(None, None, None)


@pytest.mark.asyncio
async def test_on_save_metadata_button_activates_save_action(running_app):
    main_window = _main_window(running_app)
    main_window.readme_source_view.get_buffer().set_text("desc: hello\n")
    with patch.object(main_window, "activate_action") as activate:
        main_window.on_save_metadata_button_clicked(None)
    activate.assert_called_once()
    assert activate.call_args.args[0] == "save-metadata"
    assert "desc: hello" in activate.call_args.args[1].get_string()


@pytest.mark.asyncio
async def test_linting_errors_button_shows_dialog_only_with_problems(running_app):
    main_window = _main_window(running_app)

    main_window.linting_problems = ["problem A", "problem B"]
    with patch.object(main_window.error_linting_dialog, "set_error_text") as set_text, \
            patch.object(main_window.error_linting_dialog, "show") as show:
        main_window.on_linting_errors_button_clicked(None)
        set_text.assert_called_once()
        show.assert_called_once()

    main_window.linting_problems = []
    with patch.object(main_window.error_linting_dialog, "show") as show:
        main_window.on_linting_errors_button_clicked(None)
        show.assert_not_called()


@pytest.mark.asyncio
async def test_error_bar_handlers_hide_the_bar(running_app):
    main_window = _main_window(running_app)
    # Assert on the resulting call rather than an exact count: an info-bar log
    # handler may also toggle set_revealed when records are emitted, so the count
    # is not stable across the full suite (it depends on the active log level).
    with patch.object(main_window.error_bar, "set_revealed") as set_revealed:
        main_window.on_error_bar_close(None)
        set_revealed.assert_called_with(False)

        set_revealed.reset_mock()
        main_window.on_error_bar_response(None, Gtk.ResponseType.CLOSE)
        set_revealed.assert_called_with(False)

        set_revealed.reset_mock()
        main_window.on_error_bar_response(None, Gtk.ResponseType.OK)
        set_revealed.assert_not_called()


@pytest.mark.asyncio
async def test_sort_order_switch_sets_state_and_refreshes(running_app):
    main_window = _main_window(running_app)
    with patch.object(main_window, "activate_action") as activate:
        main_window.on_sort_order_switch_state_set(None, True)
        assert main_window.search_state.sort_order == [-1]
        main_window.on_sort_order_switch_state_set(None, False)
        assert main_window.search_state.sort_order == [1]
    assert all(c.args[0] == "show-current-page" for c in activate.call_args_list)


@pytest.mark.asyncio
async def test_combo_box_handlers_update_search_state(running_app):
    main_window = _main_window(running_app)
    active = object()

    per_page_widget = MagicMock()
    per_page_widget.get_active_iter.return_value = active
    per_page_widget.get_model.return_value = {active: [20, "20"]}

    sort_field_widget = MagicMock()
    sort_field_widget.get_active_iter.return_value = active
    sort_field_widget.get_model.return_value = {active: ["name", "name"]}

    with patch.object(main_window, "activate_action") as activate:
        main_window.on_contents_per_page_combo_box_changed(per_page_widget)
        main_window.on_sort_field_combo_box_changed(sort_field_widget)

    assert main_window.search_state.page_size == 20
    assert main_window.search_state.sort_fields == ["name"]
    activated = [c.args[0] for c in activate.call_args_list]
    assert activated == ["show-first-page", "show-current-page"]


@pytest.mark.asyncio
async def test_on_copy_clicked_activates_copy_dataset(running_app):
    main_window = _main_window(running_app)

    # No selection -> nothing happens.
    with patch.object(main_window.dataset_list_box, "get_selected_row",
                      return_value=None), \
            patch.object(main_window, "activate_action") as activate:
        main_window.on_copy_clicked(MagicMock())
        activate.assert_not_called()

    # With a selection -> copy-dataset action with (source, destination).
    row = MagicMock()
    row.dataset = "file:///src"
    widget = MagicMock()
    widget.destination = "s3://dest"
    with patch.object(main_window.dataset_list_box, "get_selected_row",
                      return_value=row), \
            patch.object(main_window, "activate_action") as activate:
        main_window.on_copy_clicked(widget)
        activate.assert_called_once()
        assert activate.call_args.args[0] == "copy-dataset"
        source, destination = activate.call_args.args[1].unpack()
        assert source == "file:///src"
        assert destination == "s3://dest"
