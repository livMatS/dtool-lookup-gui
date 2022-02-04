#
# Copyright 2021 Lars Pastewka
#           2021 Johannes Hörmann
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
import os
import shutil
import traceback
import urllib.parse
from functools import reduce

from gi.repository import Gio, GLib, Gtk, GtkSource

import dtoolcore.utils
from dtool_info.utils import sizeof_fmt

import dtool_lookup_api.core.config
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient
# As of dtool-lookup-api 0.5.0, the following line still is a necessity to
# disable prompting for credentials on the command line. This behavior
# will change in future versions.
dtool_lookup_api.core.config.Config.interactive = False

from ..models.base_uris import all, LocalBaseURIModel
from ..models.datasets import DatasetModel
from ..models.settings import settings
from ..utils.copy_manager import CopyManager
from ..utils.date import date_to_string
from ..utils.dependency_graph import DependencyGraph
from ..utils.logging import FormattedSingleMessageGtkInfoBarHandler, DefaultFilter
from ..utils.query import (is_valid_query, dump_single_line_query_text)
from ..widgets.base_uri_row import DtoolBaseURIRow
from ..widgets.search_popover import DtoolSearchPopover
from ..widgets.search_results_row import DtoolSearchResultsRow
from .dataset_name_dialog import DatasetNameDialog
from .settings_dialog import SettingsDialog
from .log_window import LogWindow

_logger = logging.getLogger(__name__)


def _fill_manifest_tree_store(store, manifest, parent=None):
    nodes = {}

    store.clear()

    def find_or_create_parent_node(path, top_parent):
        if not path:
            return top_parent
        try:
            return nodes[path]
        except KeyError:
            head, tail = os.path.split(path)
            parent = find_or_create_parent_node(head, top_parent)
            new_node = store.append(parent, [tail, '', '', ''])
            nodes[path] = new_node
            return new_node

    for uuid, values in sorted(manifest, key=lambda kv: kv[1]['relpath']):
        head, tail = os.path.split(values['relpath'])
        store.append(find_or_create_parent_node(head, parent),
                     [tail,
                      sizeof_fmt(values['size_in_bytes']).strip(),
                      f'{date_to_string(values["utc_timestamp"])}',
                      uuid])


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/main_window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DtoolMainWindow'

    _max_nb_datasets = 100

    create_dataset_button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    search_entry = Gtk.Template.Child()

    #copy_dataset_spinner = Gtk.Template.Child()

    base_uri_list_box = Gtk.Template.Child()
    dataset_list_box = Gtk.Template.Child()

    main_stack = Gtk.Template.Child()
    main_paned = Gtk.Template.Child()
    main_label = Gtk.Template.Child()
    main_spinner = Gtk.Template.Child()

    dataset_stack = Gtk.Template.Child()
    dataset_box = Gtk.Template.Child()
    dataset_label = Gtk.Template.Child()

    uuid_label = Gtk.Template.Child()
    uri_label = Gtk.Template.Child()
    name_label = Gtk.Template.Child()
    created_by_label = Gtk.Template.Child()
    frozen_at_label = Gtk.Template.Child()
    size_label = Gtk.Template.Child()

    show_button = Gtk.Template.Child()
    add_items_button = Gtk.Template.Child()
    freeze_button = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()

    progress_revealer = Gtk.Template.Child()
    progress_button = Gtk.Template.Child()
    progress_popover = Gtk.Template.Child()

    edit_readme_switch = Gtk.Template.Child()
    save_metadata_button = Gtk.Template.Child()

    dependency_stack = Gtk.Template.Child()
    dependency_view = Gtk.Template.Child()
    dependency_spinner = Gtk.Template.Child()
    dependency_graph_widget = Gtk.Template.Child()

    readme_source_view = Gtk.Template.Child()
    readme_spinner = Gtk.Template.Child()
    readme_stack = Gtk.Template.Child()
    readme_view = Gtk.Template.Child()

    manifest_spinner = Gtk.Template.Child()
    manifest_stack = Gtk.Template.Child()
    manifest_tree_view = Gtk.Template.Child()
    manifest_tree_store = Gtk.Template.Child()
    manifest_view = Gtk.Template.Child()

    settings_button = Gtk.Template.Child()

    error_bar = Gtk.Template.Child()
    error_label = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.application = self.get_application()

        self.main_stack.set_visible_child(self.main_label)
        self.dataset_stack.set_visible_child(self.dataset_label)

        self.readme_buffer = self.readme_source_view.get_buffer()
        lang_manager = GtkSource.LanguageManager()
        self.readme_buffer.set_language(lang_manager.get_language("yaml"))
        self.readme_buffer.set_highlight_syntax(True)
        self.readme_buffer.set_highlight_matching_brackets(True)

        self.error_bar.set_revealed(False)
        self.progress_revealer.set_reveal_child(False)

        # connect log handler to error bar
        root_logger = logging.getLogger()
        self.log_handler = FormattedSingleMessageGtkInfoBarHandler(info_bar=self.error_bar, label=self.error_label)
        # exclude unwanted log messages from being displayed in error bar
        self.log_handler.addFilter(DefaultFilter())
        root_logger.addHandler(self.log_handler)

        # connect a search popover with search entry
        self.search_popover = DtoolSearchPopover(search_entry=self.search_entry)
        self.log_window = LogWindow(application=self.application)

        # window-scoped actions

        # search action
        search_text_variant = GLib.Variant.new_string("dummy")
        search_action = Gio.SimpleAction.new("search", search_text_variant.get_type())
        search_action.connect("activate", self.do_search)
        self.add_action(search_action)

        # select row by row index in dataset list box action
        row_index_variant = GLib.Variant.new_uint32(0)
        select_dataset_action = Gio.SimpleAction.new("select-dataset", row_index_variant.get_type())
        select_dataset_action.connect("activate", self.do_select_dataset_row_by_row_index)
        self.add_action(select_dataset_action)

        # select row by uri in dataset list box action
        uri_variant = GLib.Variant.new_string('dummy')
        select_dataset_by_uri_action = Gio.SimpleAction.new("select-dataset-by-uri", uri_variant.get_type())
        select_dataset_by_uri_action.connect("activate", self.do_select_dataset_row_by_uri)
        self.add_action(select_dataset_by_uri_action)

        # show details of dataset by row index in dataset list box action
        row_index_variant = GLib.Variant.new_uint32(0)
        show_dataset_action = Gio.SimpleAction.new("show-dataset", row_index_variant.get_type())
        show_dataset_action.connect("activate", self.do_show_dataset_details_by_row_index)
        self.add_action(show_dataset_action)

        # show details of dataset by uri in dataset list box action
        uri_variant = GLib.Variant.new_string("dummy")
        show_dataset_by_uri_action = Gio.SimpleAction.new("show-dataset-by-uri", uri_variant.get_type())
        show_dataset_by_uri_action.connect("activate", self.do_show_dataset_details_by_uri)
        self.add_action(show_dataset_by_uri_action)

        # search, select and show first search result subsequently
        row_index_variant = GLib.Variant.new_string("dummy")
        search_select_show_action = Gio.SimpleAction.new("search-select-show", row_index_variant.get_type())
        search_select_show_action.connect("activate", self.do_search_select_and_show)
        self.add_action(search_select_show_action)

        # get item
        dest_file_variant = GLib.Variant.new_string("dummy")
        get_item_action = Gio.SimpleAction.new("get-item", dest_file_variant.get_type())
        get_item_action.connect("activate", self.do_get_item)
        self.add_action(get_item_action)

        self.dependency_graph_widget.search_by_uuid = self._search_by_uuid

        self._copy_manager = CopyManager(self.progress_revealer, self.progress_popover)

        _logger.debug(f"Constructed main window for app '{self.application.get_application_id()}'")

    # utility methods
    def refresh(self):
        asyncio.create_task(self.base_uri_list_box.refresh())

    # removed these utility functions from inner scope of on_search_activate
    # in order to decouple actual signal handler and functionality
    def _update_search_summary(self, datasets):
        row = self.base_uri_list_box.search_results_row
        total_size = sum([0 if dataset.size_int is None else dataset.size_int for dataset in datasets])
        row.info_label.set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')

    async def _fetch_search_results(self, keyword, on_show=None):
        row = self.base_uri_list_box.search_results_row
        row.start_spinner()

        try:
            # datasets = await DatasetModel.search(keyword)
            if keyword:
                if is_valid_query(keyword):
                    _logger.debug("Valid query specified.")
                    datasets = await DatasetModel.query(keyword)
                else:
                    _logger.debug("Specified search text is not a valid query, just perform free text search.")
                    # NOTE: server side allows a dict with the key-value pairs
                    # "free_text", "creator_usernames", "base_uris", "uuids", "tags",
                    # via route '/dataset/search', where all except "free_text"
                    # can be lists and are translated to logical "and" or "or"
                    # constructs on the server side. With the special treatment
                    # of the 'uuid' keyword above, should we introduce similar
                    # options for the other available keywords?
                    datasets = await DatasetModel.search(keyword)
            else:
                _logger.debug("No keyword specified, list all datasets.")
                datasets = await DatasetModel.query_all()

            if len(datasets) > self._max_nb_datasets:
                _logger.warning(
                    f"{len(datasets)} search results exceed allowed displayed maximum of {self._max_nb_datasets}. "
                    f"Only the first {self._max_nb_datasets} results are shown. Narrow down your search.")
            datasets = datasets[:self._max_nb_datasets]  # Limit number of datasets that are shown
            row.search_results = datasets  # Cache datasets
            self._update_search_summary(datasets)
            if self.base_uri_list_box.get_selected_row() == row:
                # Only update if the row is still selected
                self.dataset_list_box.fill(datasets, on_show=on_show)

        except Exception as e:
            self.show_error(e)

        self.base_uri_list_box.select_search_results_row()
        self.main_stack.set_visible_child(self.main_paned)
        row.stop_spinner()

    def _search_by_uuid(self, uuid):
        search_text = dump_single_line_query_text({"uuid": uuid})
        self._search_by_search_text(search_text)

    def _search_by_search_text(self, search_text):
        self.activate_action('search-select-show', GLib.Variant.new_string(search_text))

    # utility methods - dataset selection
    def _select_dataset_row_by_row_index(self, index):
        """Select dataset row in dataset list box by index."""
        row = self.dataset_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"{row} selected.")
            self.dataset_list_box.select_row(row)
        else:
            _logger.info(f"No row with index {index} available for selection.")

    def _select_dataset_row_by_uri(self, uri):
        """Select dataset row in dataset list box by uri."""
        index = self.dataset_list_box.get_row_index_from_uri(uri)
        self._select_dataset_row_by_row_index(index)

    def _show_dataset_details(self, dataset):
        asyncio.create_task(self._update_dataset_view(dataset))
        self.dataset_stack.set_visible_child(self.dataset_box)

    def _show_dataset_details_by_row_index(self, index):
        row = self.dataset_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"{row.dataset.name} shown.")
            self._show_dataset_details(row.dataset)
        else:
            _logger.info(f"No row with index {index} available for selection.")

    def _show_dataset_details_by_uri(self, uri):
        """Select dataset row in dataset list box by uri."""
        index = self.dataset_list_box.get_row_index_from_uri(uri)
        self._show_dataset_details_by_row_index(index)

    def _select_and_show_by_row_index(self, index=0):
        self._select_dataset_row_by_row_index(index)
        self._show_dataset_details_by_row_index(index)

    def _select_and_show_by_uri(self, uri):
        self._select_dataset_row_by_uri(uri)
        self._show_dataset_details_by_uri(uri)

    def _search(self, search_text, on_show=None):
        _logger.debug(f"Evoke search with search text {search_text}.")
        self.main_stack.set_visible_child(self.main_spinner)
        row = self.base_uri_list_box.search_results_row
        row.search_results = None
        asyncio.create_task(self._fetch_search_results(search_text, on_show))

    def _search_select_and_show(self, search_text):
        _logger.debug(f"Search '{search_text}'...")
        self._search(search_text, on_show=lambda _: self._select_and_show_by_row_index())

    def _get_selected_items(self):
        """Returns (name uuid) tuples of items selected in manifest tree store."""
        selection = self.manifest_tree_view.get_selection()
        model, paths = selection.get_selected_rows()

        items = []
        for path in paths:
            column_iter = model.get_iter(path)
            item_name = model.get_value(column_iter, 0)
            item_uuid = model.get_value(column_iter, 3)
            items.append((item_name, item_uuid))

        return items

    # actions
    def do_search(self, action, value):
        """Evoke search tas for specific search text."""
        search_text = value.get_string()
        self._search(search_text)

    def do_select_dataset_row_by_row_index(self, action, value):
        """Select dataset row by index."""
        row_index = value.get_uint32()
        self._select_dataset_row_by_row_index(row_index)

    def do_select_dataset_row_by_uri(self, action, value):
        """Select dataset row by uri."""
        uri = value.get_string()
        self._select_dataset_row_by_uri(uri)

    def do_show_dataset_details_by_row_index(self, action, value):
        row_index = value.get_uint32()
        self._show_dataset_details_by_row_index(row_index)

    def do_show_dataset_details_by_uri(self, action, value):
        uri = value.get_string()
        self._show_dataset_details_by_uri(uri)

    def do_search_select_and_show(self, action, value):
        """Evoke search task for specific search text, select and show 1st row of resuls subsequntly."""
        search_text = value.get_string()
        self._search_select_and_show(search_text)

    def do_get_item(self, action, value):
        """Copy currently selected manifest item in currently selected dataset to specified destination."""
        dest_file = value.get_string()

        dataset = self.dataset_list_box.get_selected_row().dataset

        items = self._get_selected_items()
        if len(items) !=1:
            raise ValueError("Can only get one item at a time.")
        item_name, item_uuid = items[0]

        async def _get_item(dataset, item_uuid):
            cached_file = await dataset.get_item(item_uuid)
            shutil.copyfile(cached_file, dest_file)

        asyncio.create_task(_get_item(dataset, item_uuid))

    # signal handlers
    @Gtk.Template.Callback()
    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    @Gtk.Template.Callback()
    def on_logging_clicked(self, widget):
        self.log_window.show()

    @Gtk.Template.Callback()
    def on_base_uri_selected(self, list_box, row):
        if row is None:
            # this callback apparently gets evoked with row=None when an entry is deleted / unselected (?) from the base URI list
            return

        def update_base_uri_summary(datasets):
            total_size = sum([0 if dataset.size_int is None else dataset.size_int for dataset in datasets])
            row.info_label.set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')

        async def _select_base_uri():
            row.start_spinner()

            if isinstance(row, DtoolBaseURIRow):
                try:
                    _logger.debug(f"Selected base URI {row.base_uri}.")
                    datasets = await row.base_uri.all_datasets()
                    _logger.debug(f"Found {len(datasets)} datasets.")
                    update_base_uri_summary(datasets)
                    if self.base_uri_list_box.get_selected_row() == row:
                        # Only update if the row is still selected
                        self.dataset_list_box.fill(datasets)
                except Exception as e:
                    self.show_error(e)
                self.main_stack.set_visible_child(self.main_paned)
            elif isinstance(row, DtoolSearchResultsRow):
                _logger.debug("Selected search results.")
                # This is the search result
                if row.search_results is not None:
                    _logger.debug(f"Fill dataset list with {len(row.search_results)} search results.")
                    self.dataset_list_box.fill(row.search_results)
                    self.main_stack.set_visible_child(self.main_paned)
                else:
                    _logger.debug("No search results cached (likely first activation after app startup).")
                    _logger.debug("Mock emit search_entry activate signal once.")
                    self.main_stack.set_visible_child(self.main_label)
                    self.search_entry.emit("activate")
            else:
                raise TypeError(f"Handling of {type(row)} not implemented.")

            row.stop_spinner()
            row.task = None

        self.main_stack.set_visible_child(self.main_spinner)
        self.create_dataset_button.set_sensitive(not isinstance(row, DtoolSearchResultsRow) and
                                                 row.base_uri.editable)
        if row.task is None:
            _logger.debug("Spawn select_base_uri task.")
            row.task = asyncio.create_task(_select_base_uri())

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        """Search activated (usually by hitting Enter after typing in the search entry)."""
        search_text = self.search_entry.get_text()
        self._search_by_search_text(search_text)

    @Gtk.Template.Callback()
    def on_dataset_selected(self, list_box, row):
        if row is not None:
            row_index = row.get_index()
            _logger.debug(f"Selected row {row_index}.")
            self.activate_action('show-dataset', GLib.Variant.new_uint32(row_index))

    @Gtk.Template.Callback()
    def on_open_local_directory_clicked(self, widget):
        # File chooser dialog (select directory)
        dialog = Gtk.FileChooserDialog(
            title="Open local directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        # Attention: Avoid run method!
        # Unlike GLib, Python does not support running the EventLoop recursively.
        # Gbulb uses the GLib event loop, hence this works. If we move to another
        # implementation (e.g. https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/189)
        # that uses the asyncio event loop this will break.
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Quote from https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkfilechooser.html:
            #
            # When the user is finished selecting files in a Gtk.FileChooser, your program can get the selected names
            # either as filenames or as URIs. For URIs, the normal escaping rules are applied if the URI contains
            # non-ASCII characters.
            #
            # However, filenames are always returned in the character set specified by the G_FILENAME_ENCODING
            # environment variable.
            #
            # This means that while you can pass the result of Gtk.FileChooser::get_filename() to open() or fopen(),
            # you may not be able to directly set it as the text of a Gtk.Label widget unless you convert it first to
            # UTF-8, which all GTK+ widgets expect. You should use g_filename_to_utf8() to convert filenames into
            # strings that can be passed to GTK+ widgets.
            uri, = dialog.get_uris()
            # For using URI scheme on local paths, we have to unquote characters to be
            uri = urllib.parse.unquote(uri, encoding='utf-8', errors='replace')
            # Add directory to local inventory
            LocalBaseURIModel.add_directory(uri)
        elif response == Gtk.ResponseType.CANCEL:
            uri = None
        dialog.destroy()

        # Refresh view of base URIs
        asyncio.create_task(self.base_uri_list_box.refresh())

    @Gtk.Template.Callback()
    def on_create_dataset_clicked(self, widget):
        DatasetNameDialog(on_confirmation=self._create_dataset).show()

    @Gtk.Template.Callback()
    def on_show_clicked(self, widget):
        Gio.AppInfo.launch_default_for_uri(str(self.dataset_list_box.get_selected_row().dataset))

    @Gtk.Template.Callback()
    def on_add_items_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Add items", parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_select_multiple(True)

        # Attention: Avoid run method!
        # Unlike GLib, Python does not support running the EventLoop recursively.
        # Gbulb uses the GLib event loop, hence this works. If we move to another
        # implementation (e.g. https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/189)
        # that uses the asyncio event loop this will break.
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            uris = dialog.get_uris()
            fpaths = dialog.get_filenames()
            for fpath in fpaths:
                # uri = urllib.parse.unquote(uri, encoding='utf-8', errors='replace')
                self._add_item(fpath)
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    @Gtk.Template.Callback()
    def on_manifest_row_activated(self, tree_view, path, column):
        """Handler for "row-activated" signal.

        Signal emitted when the method gtk-tree-view-row-activated is called or the user double clicks a treeview row.
        It is also emitted when a non-editable row is selected and one of the keys: Space, Shift+Space, Return or Enter
        is pressed. (https://www.gnu.org/software/guile-gnome/docs/gtk/html/GtkTreeView.html)"""

        items = self._get_selected_items()
        if len(items) !=1:
            raise ValueError("Can only get one item at a time.")
        item_name, item_uuid = items[0]
        self._show_get_item_dialog(item_name, item_uuid)

    @Gtk.Template.Callback()
    def on_edit_readme_state_set(self, widget, state):
        self.readme_source_view.set_editable(state)
        self.save_metadata_button.set_sensitive(state)
        if not state:
            # We need to save the metadata
            text = self.readme_buffer.get_text(self.readme_buffer.get_start_iter(),
                                               self.readme_buffer.get_end_iter(),
                                               False)
            try:
                self.dataset_list_box.get_selected_row().dataset.put_readme(text)
            except Exception as e:
                self.show_error(e)

    @Gtk.Template.Callback()
    def on_save_metadata_button_clicked(self, widget):
        self.edit_readme_switch.set_state(False)

    @Gtk.Template.Callback()
    def on_freeze_clicked(self, widget):
        row = self.dataset_list_box.get_selected_row()
        dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL,
                                   f'You are about to freeze dataset "{row.dataset.name}". Items can no longer be '
                                   'added, removed or modified after freezing the dataset. (You will still be able to '
                                   'edit the metadata README.yml.) Please confirm freezing of this dataset.')
        # Attention: Avoid run method!
        # Unlike GLib, Python does not support running the EventLoop recursively.
        # Gbulb uses the GLib event loop, hence this works. If we move to another
        # implementation (e.g. https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/189)
        # that uses the asyncio event loop this will break.
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            uri = row.dataset.uri  # URI won't change in freeze process
            row.freeze()
            self.dataset_list_box.show_all()
            self.get_action_group("win").activate_action('select-dataset-by-uri', GLib.Variant.new_string(uri))
            self.get_action_group("win").activate_action('show-dataset-by-uri', GLib.Variant.new_string(uri))

    @Gtk.Template.Callback()
    def on_error_bar_close(self, widget):
        _logger.debug("Hide error bar.")
        self.error_bar.set_revealed(False)

    @Gtk.Template.Callback()
    def on_error_bar_response(self, widget, response_id):
        if response_id == Gtk.ResponseType.CLOSE:
            self.error_bar.set_revealed(False)

    def on_copy_clicked(self, widget):
        async def _copy():
            try:
                await self._copy_manager.copy(self.dataset_list_box.get_selected_row().dataset, widget.destination)
            except Exception as e:
                self.show_error(e)

        asyncio.create_task(_copy())

    def _show_get_item_dialog(self, item_name, item_uuid):
        dialog = Gtk.FileChooserDialog(
            title=f"Download item {item_uuid}: {item_name}", parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        dialog.set_current_name(item_name)
        dialog.set_do_overwrite_confirmation(True)

        # Attention: Avoid run method!
        # Unlike GLib, Python does not support running the EventLoop recursively.
        # Gbulb uses the GLib event loop, hence this works. If we move to another
        # implementation (e.g. https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/189)
        # that uses the asyncio event loop this will break.
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dest_file = dialog.get_filename()
            self.activate_action('get-item', GLib.Variant.new_string(dest_file))
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    # TODO: move to the model
    def _add_item(self, fpath):
        handle = os.path.basename(fpath)
        dataset = dtoolcore.ProtoDataSet.from_uri(self.dataset_list_box.get_selected_row().dataset.uri)
        dataset.put_item(fpath, handle)

    def _create_dataset(self, name):
        base_uri = self.base_uri_list_box.get_selected_row()
        if base_uri is not None:
            self.dataset_list_box.add_dataset(base_uri.base_uri.create_dataset(name))
            self.dataset_list_box.show_all()

    async def _update_dataset_view(self, dataset):
        _logger.debug("In _update_dataset_view.")

        self.uuid_label.set_text(dataset.uuid)
        self.uri_label.set_text(dataset.uri)
        self.name_label.set_text(dataset.name)
        self.created_by_label.set_text(dataset.creator)
        self.frozen_at_label.set_text(dataset.date)
        self.size_label.set_text(dataset.size_str.strip())

        # This binary distinction will allow manipulation of all datasets via
        # the according StorageBroker, as long as latter implements the
        # desired functionality
        if dataset.type == 'lookup':
            _logger.debug("Any other dataset access")
            self.show_button.set_sensitive(False)
            self.add_items_button.set_sensitive(False)
            self.freeze_button.set_sensitive(False)
            self.copy_button.set_sensitive(True)
        # if necessary, insert scheme-specific clauses later, i.e.
        # elif dataset.scheme == 's3', ....
        else:  # per default, treat all endpoints equally here
            _logger.debug("File system dataset access")
            self.show_button.set_sensitive(True)
            self.add_items_button.set_sensitive(not dataset.is_frozen)
            self.freeze_button.set_sensitive(not dataset.is_frozen)
            self.copy_button.set_sensitive(dataset.is_frozen)

        async def _get_readme():
            self.readme_stack.set_visible_child(self.readme_spinner)
            self.readme_buffer.set_text(await dataset.get_readme())
            self.readme_stack.set_visible_child(self.readme_view)

        async def _get_manifest():
            self.manifest_stack.set_visible_child(self.manifest_spinner)
            _fill_manifest_tree_store(self.manifest_tree_store, await dataset.get_manifest())
            self.manifest_stack.set_visible_child(self.manifest_view)

        _logger.debug("Get readme.")
        asyncio.create_task(_get_readme())
        _logger.debug("Get manifest.")
        asyncio.create_task(_get_manifest())

        if dataset.type == 'lookup':
            self.dependency_stack.show()
            _logger.debug("Selected dataset is lookup result.")
            asyncio.create_task(self._compute_dependencies(dataset))
        else:
            _logger.debug("Selected dataset is accessed directly.")
            self.dependency_stack.hide()

        await self._update_copy_button(dataset)

    async def _update_copy_button(self, selected_dataset):
        destinations = []
        for base_uri in await all():
            if str(base_uri) != str(selected_dataset.base_uri):
                destinations += [str(base_uri)]
        self.copy_button.get_popover().update(destinations, self.on_copy_clicked)

    async def _compute_dependencies(self, dataset):
        _logger.debug("Compute dependencies for dataset '{dataset.uuid}'.")
        self.dependency_stack.set_visible_child(self.dependency_spinner)

        # Compute dependency graph
        dependency_graph = DependencyGraph()
        async with ConfigurationBasedLookupClient() as lookup:
            _logger.debug("Wait for depenedency graph for '{dataset.uuid}' queried from lookup server.")
            await dependency_graph.trace_dependencies(lookup, dataset.uuid, dependency_keys=settings.dependency_keys)

        # Show message if uuids are missing
        missing_uuids = dependency_graph.missing_uuids
        if missing_uuids:
            _logger.warning('The following UUIDs were found during dependency graph calculation but are not present '
                            'in the database: {}'.format(reduce(lambda a, b: a + ', ' + b, missing_uuids)))

        self.dependency_graph_widget.graph = dependency_graph.graph
        self.dependency_stack.set_visible_child(self.dependency_view)

    def show_error(self, exception):
        _logger.error(traceback.format_exc())