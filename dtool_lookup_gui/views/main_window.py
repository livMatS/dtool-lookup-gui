#
# Copyright 2023 Ashwin Vazhappilly
#           2021-2023 Johannes Laurin Hörmann
#           2021 Lars Pastewka
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

from gi.repository import Gio, GLib, Gtk, GtkSource, Gdk

import dtoolcore.utils
from dtool_info.utils import sizeof_fmt

import dtool_lookup_api.core.config
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

import yamllint
from yamllint.config import YamlLintConfig
import yamllint.linter

# As of dtool-lookup-api 0.5.0, the following line still is a necessity to
# disable prompting for credentials on the command line. This behavior
# will change in future versions.
dtool_lookup_api.core.config.Config.interactive = False

from ..models.base_uris import all, LocalBaseURIModel
from ..models.datasets import DatasetModel
from ..models.settings import settings
from ..models.search_state import SearchState
from ..utils.copy_manager import CopyManager
from ..utils.date import date_to_string
from ..utils.dependency_graph import DependencyGraph
from ..utils.logging import FormattedSingleMessageGtkInfoBarHandler, DefaultFilter, _log_nested
from ..utils.query import (is_valid_query, dump_single_line_query_text)
from ..utils.subprocess import launch_default_app_for_uri
from ..widgets.base_uri_list_box import LOOKUP_BASE_URI
from ..widgets.base_uri_row import DtoolBaseURIRow
from ..widgets.search_popover import DtoolSearchPopover
from ..widgets.search_results_row import DtoolSearchResultsRow
from .dataset_name_dialog import DatasetNameDialog
from .about_dialog import AboutDialog
from .settings_dialog import SettingsDialog
from .server_versions_dialog import ServerVersionsDialog
from .config_details import ConfigDialog
from .login_window import LoginWindow
from .error_linting_dialog import LintingErrorsDialog
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
    version_button = Gtk.Template.Child()
    config_button = Gtk.Template.Child()

    error_bar = Gtk.Template.Child()
    error_label = Gtk.Template.Child()

    first_page_button = Gtk.Template.Child()
    decrease_page_button = Gtk.Template.Child()
    previous_page_button = Gtk.Template.Child()
    current_page_button = Gtk.Template.Child()
    next_page_button = Gtk.Template.Child()
    increase_page_button = Gtk.Template.Child()
    last_page_button = Gtk.Template.Child()

    main_statusbar = Gtk.Template.Child()
    contents_per_page_combo_box = Gtk.Template.Child()
    sort_field_combo_box = Gtk.Template.Child()
    sort_order_switch = Gtk.Template.Child()

    show_tags_box = Gtk.Template.Child()
    annotations_box = Gtk.Template.Child()

    linting_errors_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize pagination and sort parameters
        self.search_state = SearchState()

        self.application = self.get_application()

        self.main_stack.set_visible_child(self.main_label)
        self.dataset_stack.set_visible_child(self.dataset_label)

        self.readme_buffer = self.readme_source_view.get_buffer()
        lang_manager = GtkSource.LanguageManager()
        self.readme_buffer.set_language(lang_manager.get_language("yaml"))
        self.readme_buffer.set_highlight_syntax(True)
        self.readme_buffer.set_highlight_matching_brackets(True)
        self.readme_source_view.set_editable(True)

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
        self.settings_dialog = SettingsDialog(application=self.application)
        self.about_dialog = AboutDialog(application=self.application)
        self.config_details = ConfigDialog(application=self.application)
        self.server_versions_dialog = ServerVersionsDialog(application=self.application)
        self.error_linting_dialog = LintingErrorsDialog(application=self.application)

        # signal handlers
        self.readme_buffer.connect("changed", self.on_readme_buffer_changed)
        self.contents_per_page_combo_box.connect("changed", self.on_contents_per_page_combo_box_changed)
        self.sort_field_combo_box.connect("changed", self.on_sort_field_combo_box_changed)

        # populate sort field combo box

        # Create a ListStore to hold the data
        list_store = Gtk.ListStore(str, str)

        # Populate the ListStore with the labels from your dictionary
        for key, value in self.search_state.sort_field_label_dict.items():
            list_store.append([key, value])

        # Set the model for the combo box
        self.sort_field_combo_box.set_model(list_store)

        # Add a CellRendererText to display the text
        renderer_text = Gtk.CellRendererText()
        self.sort_field_combo_box.pack_start(renderer_text, True)
        self.sort_field_combo_box.add_attribute(renderer_text, "text", 1)

        # Set the active item (optional)
        self.sort_field_combo_box.set_active(0)

        # populate contents per page combo box

        # Create a ListStore to hold the data
        list_store = Gtk.ListStore(int, str)

        # Populate the ListStore with the labels from your dictionary
        for key in self.search_state.page_size_choices:
            list_store.append([key, str(key)])

        # Set the model for the combo box
        self.contents_per_page_combo_box.set_model(list_store)

        # Add a CellRendererText to display the text
        renderer_text = Gtk.CellRendererText()
        self.contents_per_page_combo_box.pack_start(renderer_text, True)
        self.contents_per_page_combo_box.add_attribute(renderer_text, "text", 1)

        # Set the active item (optional)
        self.contents_per_page_combo_box.set_active(1)

        # window-scoped actions

        # select base uri row by row index
        row_index_variant = GLib.Variant.new_uint32(0)
        select_base_uri_action = Gio.SimpleAction.new("select-base-uri", row_index_variant.get_type())
        select_base_uri_action.connect("activate", self.do_select_base_uri_row_by_row_index)
        self.add_action(select_base_uri_action)

        # select base uri row by uri
        uri_variant = GLib.Variant.new_string('dummy')
        select_base_uri_by_uri_action = Gio.SimpleAction.new("select-base-uri-by-uri", uri_variant.get_type())
        select_base_uri_by_uri_action.connect("activate", self.do_select_base_uri_row_by_uri)
        self.add_action(select_base_uri_by_uri_action)

        # show base uri row by row index
        row_index_variant = GLib.Variant.new_uint32(0)
        show_base_uri_action = Gio.SimpleAction.new("show-base-uri", row_index_variant.get_type())
        show_base_uri_action.connect("activate", self.do_show_base_uri_row_by_row_index)
        self.add_action(show_base_uri_action)

        # show base uri row by uri
        uri_variant = GLib.Variant.new_string('dummy')
        show_base_uri_by_uri_action = Gio.SimpleAction.new("show-base-uri-by-uri", uri_variant.get_type())
        show_base_uri_by_uri_action.connect("activate", self.do_show_base_uri_row_by_uri)
        self.add_action(show_base_uri_by_uri_action)

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

        # build dependency graph by row index in dataset list box action
        row_index_variant = GLib.Variant.new_uint32(0)
        build_dependency_graph_action = Gio.SimpleAction.new("build-dependency-graph", row_index_variant.get_type())
        build_dependency_graph_action.connect("activate", self.do_build_dependency_graph_by_row_index)
        self.add_action(build_dependency_graph_action)

        # show details of dataset by uri in dataset list box action
        uri_variant = GLib.Variant.new_string("dummy")
        show_dataset_by_uri_action = Gio.SimpleAction.new("show-dataset-by-uri", uri_variant.get_type())
        show_dataset_by_uri_action.connect("activate", self.do_show_dataset_details_by_uri)
        self.add_action(show_dataset_by_uri_action)

        # build dependency graph by uri in dataset list box action
        uri_variant = GLib.Variant.new_string("dummy")
        build_dependency_graph_by_uri_action = Gio.SimpleAction.new("build-dependency-graph-by-uri", uri_variant.get_type())
        build_dependency_graph_by_uri_action.connect("activate", self.do_build_dependency_graph_by_uri)
        self.add_action(build_dependency_graph_by_uri_action)

        # search, select and show first search result subsequently
        row_index_variant = GLib.Variant.new_string("dummy")
        search_select_show_action = Gio.SimpleAction.new("search-select-show", row_index_variant.get_type())
        search_select_show_action.connect("activate", self.do_search_select_and_show)
        self.add_action(search_select_show_action)

        # pagination actions
        page_index_variant = GLib.Variant.new_uint32(0)
        show_page_action = Gio.SimpleAction.new("show-page", page_index_variant.get_type())
        show_page_action.connect("activate", self.do_show_page)
        self.add_action(show_page_action)

        show_current_page_action = Gio.SimpleAction.new("show-current-page")
        show_current_page_action.connect("activate", self.do_show_current_page)
        self.add_action(show_current_page_action)

        show_first_page_action = Gio.SimpleAction.new("show-first-page")
        show_first_page_action.connect("activate", self.do_show_first_page)
        self.add_action(show_first_page_action)

        show_last_page_action = Gio.SimpleAction.new("show-last-page")
        show_last_page_action.connect("activate", self.do_show_last_page)
        self.add_action(show_last_page_action)

        show_next_page_action = Gio.SimpleAction.new("show-next-page")
        show_next_page_action.connect("activate", self.do_show_next_page)
        self.add_action(show_next_page_action)

        show_previous_page_action = Gio.SimpleAction.new("show-previous-page")
        show_previous_page_action.connect("activate", self.do_show_previous_page)
        self.add_action(show_previous_page_action)

        # get item
        dest_file_variant = GLib.Variant.new_string("dummy")
        get_item_action = Gio.SimpleAction.new("get-item", dest_file_variant.get_type())
        get_item_action.connect("activate", self.do_get_item)
        self.add_action(get_item_action)

        # put tag
        put_tag_variant = GLib.Variant.new_string('dummy')
        put_tag_action = Gio.SimpleAction.new("put-tag", put_tag_variant.get_type())
        put_tag_action.connect("activate", self.do_put_tag)
        self.add_action(put_tag_action)

        # put annotation
        put_annotation_variant_type = GLib.VariantType.new("(ss)")  # Tuple of two strings
        put_annotation_action = Gio.SimpleAction.new("put-annotation", put_annotation_variant_type)
        put_annotation_action.connect("activate", self.do_put_annotation)
        self.add_action(put_annotation_action)

        # delete tag
        delete_tag_variant = GLib.Variant.new_string('dummy')
        delete_tag_action = Gio.SimpleAction.new("delete-tag", delete_tag_variant.get_type())
        delete_tag_action.connect("activate", self.do_delete_tag)
        self.add_action(delete_tag_action)

        # delete annotation
        delete_annotation_variant = GLib.Variant.new_string('dummy')
        delete_annotation_action = Gio.SimpleAction.new("delete-annotation", delete_annotation_variant.get_type())
        delete_annotation_action.connect("activate", self.do_delete_annotation)
        self.add_action(delete_annotation_action)

        # add item
        add_item_variant = GLib.Variant.new_string("dummy")
        add_item_action = Gio.SimpleAction.new("add-item", add_item_variant.get_type())
        add_item_action.connect("activate", self.do_add_item)
        self.add_action(add_item_action)

        # create dataset
        create_dataset_variant = GLib.Variant.new_string("dummy")
        create_dataset_action = Gio.SimpleAction.new("create-dataset", create_dataset_variant.get_type())
        create_dataset_action.connect("activate", self.do_create_dataset)
        self.add_action(create_dataset_action)

        # freeze dataset
        freeze_dataset_action = Gio.SimpleAction.new("freeze-dataset")
        freeze_dataset_action.connect("activate", self.do_freeze_dataset)
        self.add_action(freeze_dataset_action)

        # refresh view
        refresh_view_action = Gio.SimpleAction.new("refresh-view")
        refresh_view_action.connect("activate", self.do_refresh_view)
        self.add_action(refresh_view_action)

        self.dependency_graph_widget.search_by_uuid = self._search_by_uuid

        self._copy_manager = CopyManager(self.progress_revealer, self.progress_popover)

        _logger.debug(f"Constructed main window for app '{self.application.get_application_id()}'")

        style_context = self.current_page_button.get_style_context()
        style_context.add_class('suggested-action')

        # Initialize linting_problems cache and make the linting_errors_button non-clickable (greyed out)
        self.linting_problems = None
        self.linting_errors_button.set_sensitive(False)

    # actions

    # dataset selection actions
    def do_select_dataset_row_by_row_index(self, action, value):
        """Select dataset row by index."""
        row_index = value.get_uint32()
        self._select_dataset_row_by_row_index(row_index)

    def do_select_dataset_row_by_uri(self, action, value):
        """Select dataset row by uri."""
        uri = value.get_string()
        self._select_dataset_row_by_uri(uri)

    def do_show_dataset_details_by_row_index(self, action, value):
        """Show dataset details by row index."""
        row_index = value.get_uint32()
        self._show_dataset_details_by_row_index(row_index)

    def do_build_dependency_graph_by_row_index(self, action, value):
        """Build the dependency graph by row index."""
        row_index = value.get_uint32()
        self._build_dependency_graph_by_row_index(row_index)

    def do_show_dataset_details_by_uri(self, action, value):
        """Show dataset details by uri."""
        uri = value.get_string()
        self._show_dataset_details_by_uri(uri)

    def do_build_dependency_graph_by_uri(self, action, value):
        """Build the dependency graph by uri."""
        uri = value.get_string()
        self._build_dependency_graph_by_uri(uri)

    # search actions
    def do_search(self, action, value):
        """Evoke search tas for specific search text."""
        search_text = value.get_string()
        self._search(search_text)

    def do_search_select_and_show(self, action, value):
        """Evoke search task for specific search text, select and show 1st row of resuls subsequntly."""
        search_text = value.get_string()
        self._search_select_and_show(search_text)

    # base uri selection actions
    def do_select_base_uri_row_by_row_index(self, action, value):
        """Select base uri row by index."""
        row_index = value.get_uint32()
        self._select_base_uri_row_by_row_index(row_index)

    def do_select_base_uri_row_by_uri(self, action, value):
        """Select base uri row by uri."""
        uri = value.get_string()
        self._select_base_uri_row_by_uri(uri)

    def do_show_base_uri_row_by_row_index(self, action, value):
        """Show base uri by row index"""
        row_index = value.get_uint32()
        self._show_base_uri_row_by_row_index(row_index)

    def do_show_base_uri_row_by_uri(self, action, value):
        """Show base uri by uri"""
        uri = value.get_string()
        self._show_base_uri_row_by_row_index(uri)

    # pagination actions
    def do_show_page(self, action, value):
        """Show page of specific index"""
        page_index = value.get_uint32()
        self._show_page(page_index)

    def do_show_current_page(self, action, value):
        """Show current page"""
        page_index = self.search_state.current_page
        self._show_page(page_index)

    def do_show_first_page(self, action, value):
        """Show first page"""
        page_index = self.search_state.first_page
        self._show_page(page_index)

    def do_show_last_page(self, action, value):
        """Show last page"""
        page_index = self.search_state.last_page
        self._show_page(page_index)

    def do_show_next_page(self, action, value):
        """Show next page"""
        page_index = self.search_state.next_page
        self._show_page(page_index)

    def do_show_previous_page(self, action, value):
        """Show previous page"""
        page_index = self.search_state.previous_page
        self._show_page(page_index)

    # put tags action
    def do_put_tag(self, action, value):
        """Put tags on the selected dataset."""
        tag = value.get_string()
        self._put_tag(tag)

    # put annotations action
    def do_put_annotation(self, action, parameter):
        """Put annotations on the selected dataset."""
        key, value = parameter.unpack()
        _logger.debug("Unpacked %s: %s key-value pair from tuple in do_put_annotation")
        self._put_annotation(key, value)

    def do_delete_tag(self, action, value):
        """Put tags on the selected dataset."""
        tag = value.get_string()
        self._delete_tag(tag)

    # put annotations action
    def do_delete_annotation(self, action, value):
        """Put annotations on the selected dataset."""
        value = value.get_string()
        self._delete_annotation(value)

    # add item action
    def do_add_item(self, action, value):
        """Add item to the selected dataset."""
        item = value.get_string()
        self._add_item(item)
    
    # create dataset action
    def do_create_dataset(self, action, value):
        """Create a new dataset."""
        self._create_dataset(value.get_string())

    # freeze dataset action
    def do_freeze_dataset(self, action, value):
        """Freeze the selected dataset."""
        self._freeze_dataset()

    # other actions
    def do_get_item(self, action, value):
        """"Copy currently selected manifest item in currently selected dataset to specified destination."""

        dest_file = value.get_string()

        dataset = self.dataset_list_box.get_selected_row().dataset

        items = self._get_selected_items()
        if len(items) != 1:
            raise ValueError("Can only get one item at a time.")
        item_name, item_uuid = items[0]

        async def _get_item(dataset, item_uuid):
            cached_file = await dataset.get_item(item_uuid)
            shutil.copyfile(cached_file, dest_file)

            if settings.open_downloaded_item:
                # try to launch default application for downloaded item if desired
                _logger.debug("Try to open '%s' with default application.", dest_file)
                launch_default_app_for_uri(dest_file)

        asyncio.create_task(_get_item(dataset, item_uuid))

    def do_refresh_view(self, action, value):
        """Refresh view by reloading base uri list, """
        self.refresh()

    # signal handlers

    @Gtk.Template.Callback()
    def on_settings_clicked(self, widget):
        """Setting menu item clicked."""
        self.settings_dialog.show()

    @Gtk.Template.Callback()
    def version_button_clicked(self, widget):
        """Server versions menu item clicked."""
        self.server_versions_dialog.show()

    @Gtk.Template.Callback()
    def config_button_clicked(self, widget):
        """Server config menu item clicked."""
        self.config_details.show()

    @Gtk.Template.Callback()
    def on_logging_clicked(self, widget):
        """Log window menu item clicked."""
        self.log_window.show()

    @Gtk.Template.Callback()
    def on_about_clicked(self, widget):
        """About dialog menu item clicked"""
        self.about_dialog.show()

    @Gtk.Template.Callback()
    def on_base_uri_selected(self, list_box, row):
        """Entry on base URI list clicked."""
        if row is not None:
            row_index = row.get_index()
            _logger.debug(f"Selected base uri row {row_index}.")
            self.activate_action('show-base-uri', GLib.Variant.new_uint32(row_index))

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        """Search activated (usually by hitting Enter after typing in the search entry)."""
        search_text = self.search_entry.get_text()
        self.activate_action('search-select-show', GLib.Variant.new_string(search_text))

    @Gtk.Template.Callback()
    def on_search_drop_down_clicked(self, widget):
        """Drop down button next to search field clicked for opening larger popover."""
        if self.search_popover.get_visible():
            _logger.debug(
                f"Search entry drop down icon pressed, hide popover.")
            self.search_popover.popdown()
        else:
            _logger.debug(f"Search entry drop down icon pressed, show popover.")
            self.search_popover.popup_at(widget)

    @Gtk.Template.Callback()
    def on_dataset_selected(self, list_box, row):
        """Entry on dataset list clicked."""
        if row is not None:
            row_index = row.get_index()
            _logger.debug(f"Selected row {row_index}.")
            self.activate_action('show-dataset', GLib.Variant.new_uint32(row_index))

    @Gtk.Template.Callback()
    def on_open_local_directory_clicked(self, widget):
        """Open directory button as local base URI clicked."""
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
            try:
                LocalBaseURIModel.add_directory(uri)
            except ValueError as err:
                _logger.warning(str(err))
        elif response == Gtk.ResponseType.CANCEL:
            uri = None
        dialog.destroy()

        # Refresh view of base URIs
        asyncio.create_task(self._refresh_base_uri_list_box())

    @Gtk.Template.Callback()
    def on_create_dataset_clicked(self, widget):
        """Dataset creation button clicked."""
        DatasetNameDialog(on_confirmation=lambda name:self.activate_action('create-dataset', GLib.Variant.new_string(name))
).show()

    @Gtk.Template.Callback()
    def on_refresh_clicked(self, widget):
        """Refresh button clicked."""
        self.get_action_group("win").activate_action('refresh-view', None)

    @Gtk.Template.Callback()
    def on_show_clicked(self, widget):
        uri = str(self.dataset_list_box.get_selected_row().dataset)
        launch_default_app_for_uri(uri)

    @Gtk.Template.Callback()
    def on_add_items_clicked(self, widget):
        """Add items to dataset button clicked."""
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
                # self._add_item(fpath)
                self.activate_action('add-item', GLib.Variant.new_string(fpath))
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
        if len(items) != 1:
            raise ValueError("Can only get one item at a time.")
        item_name, item_uuid = items[0]
        self._show_get_item_dialog(item_name, item_uuid)

    @Gtk.Template.Callback()
    def on_save_metadata_button_clicked(self, widget):
        """Save button on edited metadata clicked."""
        # Get the YAML content from the source view
        text_buffer = self.readme_source_view.get_buffer()
        start_iter, end_iter = text_buffer.get_bounds()
        yaml_content = text_buffer.get_text(start_iter, end_iter, True)

        # Check the state of the linting switch before linting
        if settings.yaml_linting_enabled:
            # Lint the YAML content if the above condition wasn't met (i.e., linting is enabled)
            conf = YamlLintConfig('extends: default')  # using the default config
            self.linting_problems = list(yamllint.linter.run(yaml_content, conf))  # Make it an instance variable
            _logger.debug(str(self.linting_problems))
            total_errors = len(self.linting_problems)
            if total_errors > 0:
                self.linting_errors_button.set_sensitive(True)
                if total_errors == 1:
                    error_message = f"YAML Linter Error:\n{str(self.linting_problems[0])}"
                else:
                    other_errors_count = total_errors - 1  # since we're showing the first error
                    error_message = f"YAML Linter Error:\n{str(self.linting_problems[0])} and {other_errors_count} other YAML linting errors.\nClick here for more details"
                self.linting_errors_button.set_label(error_message)
            else:
                self.linting_errors_button.set_label("No linting issues found!")
                self.dataset_list_box.get_selected_row().dataset.put_readme(yaml_content)
        else:

            # Clear previous linting problems when linting is turned off
            self.linting_problems = None
            self.linting_errors_button.set_label("YAML linting turned off.")

            _logger.debug("YAML linting turned off.")
            self.dataset_list_box.get_selected_row().dataset.put_readme(yaml_content)

    @Gtk.Template.Callback()
    def on_linting_errors_button_clicked(self, widget):
        """Linting errors clicked, show extended log."""
        # Check if the problems attribute exists
        if hasattr(self, 'linting_problems') and self.linting_problems:
            # Join the linting error messages into a single string
            error_text = '\n\n'.join(str(problem) for problem in self.linting_problems)

            # Set the linting error text to the dialog
            self.error_linting_dialog.set_error_text(error_text)

            # Show the dialog
            self.error_linting_dialog.show()
        else:
            pass

    @Gtk.Template.Callback()
    def on_freeze_clicked(self, widget):
        """Freeze dataset button clicked."""
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
            # uri = row.dataset.uri  # URI won't change in freeze process
            # row.freeze()
            self.activate_action('freeze-dataset')
            self.dataset_list_box.show_all()
            # self.get_action_group("win").activate_action('select-dataset-by-uri', GLib.Variant.new_string(uri))
            # self.get_action_group("win").activate_action('show-dataset-by-uri', GLib.Variant.new_string(uri))

    @Gtk.Template.Callback()
    def on_error_bar_close(self, widget):
        """Close error bar button clicked."""
        _logger.debug("Hide error bar.")
        self.error_bar.set_revealed(False)

    @Gtk.Template.Callback()
    def on_error_bar_response(self, widget, response_id):
        if response_id == Gtk.ResponseType.CLOSE:
            self.error_bar.set_revealed(False)

    # sort signal handlers
    # @Gtk.Template.Callback()
    # def on_sort_field_combo_box_changed(self, widget):
    #     sort_field = widget.get_active_text()
    #     _logger.debug("sort field changed to %s", sort_field)

    @Gtk.Template.Callback()
    def on_sort_order_switch_state_set(self, widget, state):
        """Sort order ascending&/descending switch toggled."""
        # Toggle sort order based on the switch state
        if state:
            sort_order = -1  # Switch is on, use ascending order
        else:
            sort_order = 1  # Switch is off, use descending order

        self.search_state.sort_order = [sort_order]
        self.activate_action('show-current-page')
        # self.on_sort_field_combo_box_changed(self.sort_field_combo_box)

    @Gtk.Template.Callback()
    def on_contents_per_page_combo_box_changed(self, widget):
        """Contents per page combo box entry changed."""
        # Get the active iter and retrieve the key from the first column
        model = widget.get_model()
        active_iter = widget.get_active_iter()
        if active_iter is not None:
            selected_key = model[active_iter][0]  # This is the key

        self.search_state.page_size = selected_key
        self.activate_action('show-first-page')

    @Gtk.Template.Callback()
    def on_sort_field_combo_box_changed(self, widget):
        """Sort field combo box entry changed."""
        # Get the active iter and retrieve the key from the first column
        model = widget.get_model()
        active_iter = widget.get_active_iter()
        if active_iter is not None:
            selected_key = model[active_iter][0]  # This is the key

        self.search_state.sort_fields = [selected_key]
        self.activate_action('show-current-page')

    # pagination signal handlers

    @Gtk.Template.Callback()
    def on_first_page_button_clicked(self, widget):
        """Navigate to the first page"""
        self.activate_action('show-first-page')

    @Gtk.Template.Callback()
    def on_decrease_page_button_clicked(self, widget):
        """Navigate to the previous page if it exists"""
        self.activate_action('show-previous-page')

    @Gtk.Template.Callback()
    def on_previous_page_button_clicked(self, widget):
        """Navigate to the previous page if it exists"""
        self.activate_action('show-previous-page')

    @Gtk.Template.Callback()
    def on_current_page_button_clicked(self, widget):
        """Highlight the current page button and fetch its results"""
        style_context = self.current_page_button.get_style_context()
        style_context.add_class('suggested-action')
        self.activate_action('show-current-page')

    @Gtk.Template.Callback()
    def on_next_page_button_clicked(self, widget):
        # Navigate to the next page if available
        self.activate_action('show-next-page')

    @Gtk.Template.Callback()
    def on_increase_page_button_clicked(self, widget):
        """Navigate to the next page uif it exists"""
        self.activate_action('show-next-page')

    @Gtk.Template.Callback()
    def on_last_page_button_clicked(self, widget):
        """Navigate to the last page"""
        self.activate_action('show-last-page')
        
    def on_readme_buffer_changed(self, buffer):
        self.save_metadata_button.set_sensitive(True)

    # TODO: this should be an action do_copy
    # if it is possible to hand two strings, e.g. source and destination to an action, then this action should
    # go to the main app.
    # @Gtk.Template.Callback(), not in .ui
    def on_copy_clicked(self, widget):
        """Dataset copy button clicked."""
        async def _copy():
            try:
                await self._copy_manager.copy(self.dataset_list_box.get_selected_row().dataset, widget.destination)
            except Exception as e:
                self.show_error(e)

        asyncio.create_task(_copy())

    # public methods

    def refresh(self):
        """Refresh view."""

        dataset_row = self.dataset_list_box.get_selected_row()
        dataset_uri = None
        if dataset_row is not None:
            dataset_uri = dataset_row.dataset.uri
            _logger.debug(f"Keep '{dataset_uri}' for dataset refresh.")

        async def _refresh():
            # first, refresh base uri list and its selection
            await self._refresh_base_uri_list_box()
            self._select_and_load_first_uri()

            _logger.debug(f"Done refreshing base URIs.")
            # on_base_uri_selected(self, list_box, row) called by selection
            # above already

            # TODO: following restoration of selected dataset needs to happen
            # after base URI has been loaded, but on_base_uri_selected
            # spawns another task, hence above "await" won't wait for the
            # process to complete. Need a signal instead.
            # if dataset_uri is not None:
            #    _logger.debug(f"Select and show '{dataset_uri}'.")
            #    self._select_and_show_by_uri(dataset_uri)

        asyncio.create_task(_refresh())

    def show_error(self, exception):
        _logger.error(traceback.format_exc())

    # private methods

    async def _refresh_base_uri_list_box(self):
        # book keeping of current state
        base_uri_row = self.base_uri_list_box.get_selected_row()
        base_uri = None

        if isinstance(base_uri_row, DtoolBaseURIRow):
            base_uri = str(base_uri_row.base_uri)
        elif isinstance(base_uri_row, DtoolSearchResultsRow):
            base_uri = LOOKUP_BASE_URI

        # first, refresh list box
        await self.base_uri_list_box.refresh()
        # second, refresh base uri list selection
        if base_uri is not None:
            _logger.debug(f"Reselect base URI '{base_uri}")
            self._select_base_uri_row_by_uri(base_uri)

    # removed these utility functions from inner scope of on_search_activate
    # in order to decouple actual signal handler and functionality
    def _update_search_summary(self, datasets):
        row = self.base_uri_list_box.search_results_row
        total_value = self.search_state.total_number_of_entries
        row.info_label.set_text(f'{total_value} datasets')

    def _update_main_statusbar(self, datasets):
        total_number = self.search_state.total_number_of_entries
        current_page = self.search_state.current_page
        last_page = self.search_state.last_page
        page_size = self.search_state.page_size
        total_size = sum([0 if dataset.size_int is None else dataset.size_int for dataset in datasets])
        self.main_statusbar.push(0,
                                 f"{total_number} datasets in total at {page_size} per page, "
                                 f"{sizeof_fmt(total_size).strip()} total size of {len(datasets)} datasets on current page, "
                                 f"on page {current_page} of {last_page}")

    async def _fetch_search_results(self, on_show=None):
        """Retrieve search results from lookup server."""

        self.search_state.fetching_results = True
        self._disable_pagination_buttons()

        # Here sort order 1 implies ascending
        row = self.base_uri_list_box.search_results_row
        row.start_spinner()
        self.main_spinner.start()

        pagination = {}
        sorting = {}
        try:
            if self.search_state.search_text:
                if is_valid_query(self.search_state.search_text):
                    _logger.debug("Valid query specified.")
                    datasets = await DatasetModel.get_datasets_by_mongo_query(
                        query=self.search_state.search_text,
                        page_number=self.search_state.current_page,
                        page_size=self.search_state.page_size,
                        sort_fields=self.search_state.sort_fields,
                        sort_order=self.search_state.sort_order,
                        pagination=pagination,
                        sorting=sorting

                    )
                else:
                    _logger.debug("Specified search text is not a valid query, just perform free text search.")
                    datasets = await DatasetModel.get_datasets(
                        free_text=self.search_state.search_text,
                        page_number=self.search_state.current_page,
                        page_size=self.search_state.page_size,
                        sort_fields=self.search_state.sort_fields,
                        sort_order=self.search_state.sort_order,
                        pagination=pagination,
                        sorting=sorting
                    )
            else:
                _logger.debug("No keyword specified, list all datasets.")
                datasets = await DatasetModel.get_datasets(
                    page_number=self.search_state.current_page,
                    page_size=self.search_state.page_size,
                    sort_fields=self.search_state.sort_fields,
                    sort_order=self.search_state.sort_order,
                    pagination=pagination,
                    sorting=sorting
                )

            self.search_state.ingest_pagination_information(pagination)
            self.search_state.ingest_sorting_information(sorting)

            if len(datasets) > self._max_nb_datasets:
                _logger.warning(
                    f"{len(datasets)} search results exceed allowed displayed maximum of {self._max_nb_datasets}. "
                    f"Only the first {self._max_nb_datasets} results are shown. Narrow down your search."
                )
                datasets = datasets[:self._max_nb_datasets]  # Limit number of datasets that are shown

            row.search_results = datasets  # Cache datasets

            self._update_search_summary(datasets)
            self._update_main_statusbar(datasets)

            if self.base_uri_list_box.get_selected_row() == row:
                # Only update if the row is still selected
                self.dataset_list_box.fill(datasets, on_show=on_show)
        except RuntimeError as e:
            # TODO: There should probably be a more explicit test on authentication failure.
            self.show_error(e)

            async def retry():
                await asyncio.sleep(
                    0.5)  # TODO: This is a dirty workaround for not having the login window pop up twice
                await self._fetch_search_results(on_show=on_show)

            # What happens is that the LoginWindow evokes the renew-token action via Gtk framework.
            # This happens asynchronously as well. This means _fetch_search_results called again
            # within the retry() function would open another LoginWindow here as the token renewal does
            # not happen "quick" enough. Hence there is the asyncio.sleep(1).
            LoginWindow(application=self.application, follow_up_action=lambda: asyncio.create_task(retry())).show()

        except Exception as e:
            self.show_error(e)

        self.base_uri_list_box.select_search_results_row()
        self.main_stack.set_visible_child(self.main_paned)
        row.stop_spinner()
        self.main_spinner.stop()

        self._update_pagination_buttons()
        self.search_state.fetching_results = False

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
            _logger.debug(f"Dataset row {index} selected.")
            self.dataset_list_box.select_row(row)
        else:
            _logger.info(f"No dataset row with index {index} available for selection.")

    def _select_dataset_row_by_uri(self, uri):
        """Select dataset row in dataset list box by uri."""
        index = self.dataset_list_box.get_row_index_from_uri(uri)
        self._select_dataset_row_by_row_index(index)

    def _show_dataset_details(self, dataset):
        """Kick off asynchronous task to show dataset details."""
        asyncio.create_task(self._update_dataset_view(dataset))
        self.dataset_stack.set_visible_child(self.dataset_box)

    def _build_dependency_graph(self, dataset):
        """Kick off asynchronous task to build dependency graph."""
        asyncio.create_task(self._compute_dependencies(dataset))

    def _show_dataset_details_by_row_index(self, index):
        """Show dataset details by row index."""
        row = self.dataset_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"{row.dataset.name} shown.")
            self._show_dataset_details(row.dataset)
        else:
            _logger.info(f"No dataset row with index {index} available for selection.")

    def _build_dependency_graph_by_row_index(self, index):
        """Build dependency graph by row index."""
        row = self.dataset_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"{row.dataset.name} shown.")
            self._build_dependency_graph(row.dataset)
        else:
            _logger.info(f"No dataset row with index {index} available for selection.")

    def _show_dataset_details_by_uri(self, uri):
        """Select dataset row in dataset list box by uri."""
        index = self.dataset_list_box.get_row_index_from_uri(uri)
        self._show_dataset_details_by_row_index(index)

    def _build_dependency_graph_by_uri(self, uri):
        """Build dependency graph by uri."""
        index = self.dataset_list_box.get_row_index_from_uri(uri)
        self._build_dependency_graph_by_row_index(index)

    def _select_and_show_by_row_index(self, index=0):
        """Select dataset entry by row index and show details."""
        self._select_dataset_row_by_row_index(index)
        self._show_dataset_details_by_row_index(index)

    def _select_and_show_by_uri(self, uri):
        """Select dataset entry by URI and show details."""
        self._select_dataset_row_by_uri(uri)
        self._show_dataset_details_by_uri(uri)

    def _search(self, search_text, on_show=None):
        """Get datasets by text search."""
        self.search_state.search_text = search_text
        self.search_state.reset_pagination()
        self._refresh_datasets(on_show=on_show)
    
    # put tags function for action
    def _put_tag(self, tags):
        """Put tags on the selected dataset."""
        dataset = self.dataset_list_box.get_selected_row().dataset
        dataset.put_tag(tags)
        asyncio.create_task(self._update_dataset_view(dataset))

    # put annotations function for action
    def _put_annotation(self, key, value):
        """Put annotations on the selected dataset."""
        dataset = self.dataset_list_box.get_selected_row().dataset
        dataset.put_annotation(annotation_name=key, annotation=value)
        asyncio.create_task(self._update_dataset_view(dataset))

    def _delete_tag(self, tag):
        """Put tags on the selected dataset."""
        dataset = self.dataset_list_box.get_selected_row().dataset
        dataset.delete_tag(tag)
        asyncio.create_task(self._update_dataset_view(dataset))

    def _delete_annotation(self, annotation_name):
        """Put annotations on the selected dataset."""
        dataset = self.dataset_list_box.get_selected_row().dataset
        dataset.delete_annotation(annotation_name)
        asyncio.create_task(self._update_dataset_view(dataset))

    def _refresh_datasets(self, on_show=None):
        """Reset dataset list, show spinner, and kick off async task for retrieving dataset entries."""
        self.main_stack.set_visible_child(self.main_spinner)
        row = self.base_uri_list_box.search_results_row
        row.search_results = None
        asyncio.create_task(self._fetch_search_results(on_show=on_show))

    def _search_select_and_show(self, search_text):
        """Get datasets by text search, select first row and show dataset details."""
        _logger.debug(f"Search '{search_text}'...")
        self._search(search_text, on_show=lambda _: self._select_and_show_by_row_index())

    # pagination functionality
    def _show_page(self, page_index):
        """Get datasets by page, select first row and show dataset details."""
        if not self.search_state.fetching_results:
            self.search_state.current_page = page_index
            self._refresh_datasets(on_show=lambda _: self._select_and_show_by_row_index())

    def _update_pagination_buttons(self):
        """Update pagination buttons to match current search state."""

        self.current_page_button.set_sensitive(True)
        self.current_page_button.set_label(str(self.search_state.current_page))

        if self.search_state.current_page >= self.search_state.last_page:
            self.next_page_button.set_label('')
            self.next_page_button.set_sensitive(False)
            self.increase_page_button.set_sensitive(False)
            self.last_page_button.set_sensitive(False)
        else:
            self.next_page_button.set_label(str(self.search_state.next_page))
            self.next_page_button.set_sensitive(True)
            self.increase_page_button.set_sensitive(True)
            self.last_page_button.set_sensitive(True)

        if self.search_state.current_page <= self.search_state.first_page:
            self.previous_page_button.set_label('')
            self.previous_page_button.set_sensitive(False)
            self.decrease_page_button.set_sensitive(False)
            self.first_page_button.set_sensitive(False)
        else:
            self.previous_page_button.set_label(str(self.search_state.previous_page))
            self.previous_page_button.set_sensitive(True)
            self.decrease_page_button.set_sensitive(True)
            self.first_page_button.set_sensitive(True)

    def _disable_pagination_buttons(self):
        """Disable all pagination buttons (typically while fetching results)"""
        self.first_page_button.set_sensitive(False)
        self.next_page_button.set_sensitive(False)
        self.last_page_button.set_sensitive(False)
        self.previous_page_button.set_sensitive(False)
        self.current_page_button.set_sensitive(False)
        self.decrease_page_button.set_sensitive(False)
        self.increase_page_button.set_sensitive(False)

    # other helper functions
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

    # utility methods - base uri selection
    def _select_base_uri_row_by_row_index(self, index):
        """Select base uri row in base uri list box by index."""
        row = self.base_uri_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"Base URI row {index} selected.")
            self.base_uri_list_box.select_row(row)
        else:
            _logger.info(f"No base URI row with index {index} available for selection.")

    def _select_base_uri_row_by_uri(self, uri):
        """Select base uri row in dataset list box by uri."""
        index = self.base_uri_list_box.get_row_index_from_uri(uri)
        self._select_base_uri_row_by_row_index(index)

    def _show_base_uri_row_by_row_index(self, index):
        """Select base uri row in dataset list box by uri."""
        row = self.base_uri_list_box.get_row_at_index(index)
        if row is not None:
            _logger.debug(f"Base URI row {index} selected.")
            self.base_uri_list_box.select_row(row)
            self._show_base_uri(row, on_show=lambda _: self._select_and_show_by_row_index())
        else:
            _logger.info(f"No base URI row with index {index} available for selection.")

    def _show_base_uri_row_by_uri(self, uri):
        """Select base uri row in dataset list box by uri."""
        self._select_base_uri_row_by_uri(uri)

        # index = self.base_uri_list_box.get_row_index_from_uri(uri)
        # self._select_base_uri_row_by_row_index(index)

    def _show_base_uri(self, row, on_show=None):
        """Show datasets in selected base URI."""
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
                       self.dataset_list_box.fill(datasets, on_show=on_show)
                except Exception as e:
                    self.show_error(e)
                self.main_stack.set_visible_child(self.main_paned)
            elif isinstance(row, DtoolSearchResultsRow):
                _logger.debug("Selected search results.")
                # This is the search result
                if row.search_results is not None:
                    _logger.debug(f"Fill dataset list with {len(row.search_results)} search results.")
                    self.dataset_list_box.fill(row.search_results, on_show=on_show)
                    self.main_stack.set_visible_child(self.main_paned)
                else:
                    _logger.debug("No search results cached (likely first activation after app startup).")
                    # _logger.debug("Mock emit search_entry activate signal once.")
                    self.main_stack.set_visible_child(self.main_label)
                    # self.search_entry.emit("activate")
                    await self._fetch_search_results(on_show=on_show)
            else:
                raise TypeError(f"Handling of {type(row)} not implemented.")

            row.stop_spinner()
            row.task = None

        self.main_stack.set_visible_child(self.main_spinner)
        self.create_dataset_button.set_sensitive(not isinstance(row, DtoolSearchResultsRow) and
                                                 row.base_uri.editable)
        self._set_lookup_gui_widgets_state(isinstance(row, DtoolSearchResultsRow))

        if row.task is None:
            _logger.debug("Spawn select_base_uri task.")
            row.task = asyncio.create_task(_select_base_uri())

    def _set_lookup_gui_widgets_state(self, state=False):
        self.search_entry.set_sensitive(state)
        self.contents_per_page_combo_box.set_sensitive(state)
        self.sort_field_combo_box.set_sensitive(state)
        self.sort_order_switch.set_sensitive(state)
        if state is True:
            self._update_pagination_buttons()
        else:
            self._disable_pagination_buttons()

    def _select_and_load_first_uri(self):
        """
        This function automatically reloads the data and selects the first URI.
        """
        first_row = self.base_uri_list_box.get_children()[0]
        self.base_uri_list_box.select_row(first_row)
        self.on_base_uri_selected(self.base_uri_list_box, first_row)

    def _show_get_item_dialog(self, item_name, item_uuid):
        default_dir = settings.item_download_directory

        if settings.choose_item_download_directory:
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

            if os.path.isdir(default_dir):
                _logger.debug("Set default download dir to '%s'.", default_dir)
                dialog.set_current_folder(default_dir)
            else:
                _logger.warning("'%s' is no valid default download dir.", default_dir)

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
        else:
            if not os.path.isdir(default_dir):
                _logger.error("'%s' is no valid download directory.", default_dir)
                return
            dest_file = os.path.join(default_dir, item_name)
            self.activate_action('get-item', GLib.Variant.new_string(dest_file))

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
    
    def _freeze_dataset(self):
        row = self.dataset_list_box.get_selected_row()
        uri = row.dataset.uri
        row.freeze()
        self.dataset_list_box.show_all()
        self.get_action_group("win").activate_action('select-dataset-by-uri', GLib.Variant.new_string(uri))
        self.get_action_group("win").activate_action('show-dataset-by-uri', GLib.Variant.new_string(uri))

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
            self.save_metadata_button.set_sensitive(False)

        async def _get_manifest():
            self.manifest_stack.set_visible_child(self.manifest_spinner)
            _fill_manifest_tree_store(self.manifest_tree_store, await dataset.get_manifest())
            self.manifest_stack.set_visible_child(self.manifest_view)

        def on_remove_tag(self, button, tag):
            self.activate_action('delete-tag', GLib.Variant.new_string(tag))

        def on_add_tag(self, button, entry):
            tag = entry.get_text()
            self.activate_action('put-tag', GLib.Variant.new_string(tag))

        async def _get_tags():
            tags = await dataset.get_tags()

            # Remove the widgets of previous datasets already present
            for child in self.show_tags_box.get_children():
                self.show_tags_box.remove(child)

            # Loop through the tags to create and display each tag with a remove button
            for tag in tags:
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

                label = Gtk.Label(label=tag)

                # Remove button for the tag
                button = Gtk.Button(label="-")
                button.connect("clicked",
                               lambda button, tag = tag : on_remove_tag(self, button, tag))

                # Adding the label and button to the box
                box.pack_start(label, False, False, 0)
                box.pack_start(button, False, False, 0)

                # Adding the box to the show_tags_box
                self.show_tags_box.pack_start(box, False, False, 0)

            # Adding the empty text box and "+" button for adding new tags
            add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            # Text box for entering new tags
            entry = Gtk.Entry()
            entry.set_placeholder_text("Enter new tag")
            entry.set_margin_start(10)

            # "+" button for adding the new tag
            add_button = Gtk.Button(label="+")
            add_button.connect("clicked",
                               lambda button: on_add_tag(self , button, entry))

            # Adding the entry and "+" button to the add_box
            add_box.pack_start(entry, True, True, 0)
            add_box.pack_start(add_button, False, False, 0)

            # Adding the add_box to the show_tags_box
            self.show_tags_box.pack_start(add_box, False, False, 0)

            self.show_all()
        
        async def _get_annotations():
            annotations = await dataset.get_annotations()
            for child in self.annotations_box.get_children():
                self.annotations_box.remove(child)

            async def create_annotation_row(key="", value="", is_new=False):
                """Creates a single row of annotation with text boxes and a button."""
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

                # Key: Display label if not new, text entry if new
                if is_new:
                    key_widget = Gtk.Entry()
                    key_widget.set_text(key)
                    key_widget.set_max_width_chars(10)
                    key_widget.set_hexpand(False)
                    key_widget.set_placeholder_text("Enter new Key")
                else:
                    key_widget = Gtk.Label(label=key)
                    key_widget.set_max_width_chars(10)
                    key_widget.set_hexpand(False)
                
                box.pack_start(key_widget, expand=False, fill=False, padding=5)

                # Value: Display text entry for both new and existing annotations
                value_entry = Gtk.Entry()
                value_entry.set_text(value)
                value_entry.set_max_width_chars(10)
                value_entry.set_hexpand(False)
                value_entry.set_placeholder_text("Enter new Value")
                box.pack_start(value_entry, expand=False, fill=False, padding=5)

                # Button for delete/save functionality
                button = Gtk.Button(label="-" if not is_new else "+")
                
                async def on_button_clicked(button):
                    current_label = button.get_label()
                    if current_label == "-":
                        # Delete annotation
                        # self.annotations_box.remove(box)
                        # Function to delete the annotation from the dataset not yet implemented
                        # dataset.delete_annotation(key)
                        self.activate_action('delete-annotation', GLib.Variant.new_string(key))
                    elif current_label == "+":
                        # Save new/updated annotation
                        new_key = key_widget.get_text() if is_new else key
                        new_value = value_entry.get_text()
                        if new_key and new_value:
                            # Add or update annotation in dataset
                            annotation_tuple = GLib.Variant("(ss)", (new_key, new_value))
                            self.activate_action('put-annotation', annotation_tuple)
                            # dataset.put_annotation(annotation_name=new_key, annotation=new_value)
                            # button.set_label("-")  # Change to delete after saving
                            button.set_label("-")  # Change to "-" after saving
                            # asyncio.create_task(self._update_dataset_view(dataset))

                # Update button label on text change
                def on_text_changed(entry):
                    if button.get_label() == "-":
                        button.set_label("+")
                
                value_entry.connect("changed", on_text_changed)
                if is_new:
                    key_widget.connect("changed", on_text_changed)  # Only for the new key entry
                button.connect("clicked",
                               lambda btn: asyncio.ensure_future(on_button_clicked(btn)))

                # Add the button to the row
                box.pack_start(button, expand=False, fill=False, padding=0)

                return box

            # Add rows for each annotation
            for key, value in annotations.items():
                row = await create_annotation_row(key, value)
                self.annotations_box.pack_start(row, expand=False, fill=False, padding=5)

            # Always show one empty text boxes for new annotations
            for _ in range(1):
                new_row = await create_annotation_row(is_new=True)
                self.annotations_box.pack_start(new_row, expand=False, fill=False, padding=5)

            # Re-render the UI
            self.annotations_box.show_all()

        _logger.debug("Get readme.")
        asyncio.create_task(_get_readme())
        _logger.debug("Get manifest.")
        asyncio.create_task(_get_manifest())
        _logger.debug("Get tags.")
        asyncio.create_task(_get_tags())
        _logger.debug("Get annotations.")
        asyncio.create_task(_get_annotations())

        if dataset.type == 'lookup':
            self.dependency_stack.show()
            _logger.debug("Selected dataset is lookup result.")
            self.get_action_group("win").activate_action('build-dependency-graph-by-uri',
                                                         GLib.Variant.new_string(dataset.uri))
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
        _logger.debug("Compute dependencies for dataset '%s'.", dataset.uuid)
        self.dependency_stack.set_visible_child(self.dependency_spinner)

        # Compute dependency graph
        dependency_graph = DependencyGraph()
        async with ConfigurationBasedLookupClient() as lookup:
            _logger.debug("Wait for depenedency graph for '%s' queried from lookup server.", dataset.uuid)
            await dependency_graph.trace_dependencies(lookup, dataset.uuid, dependency_keys=settings.dependency_keys)

        # Show message if uuids are missing
        missing_uuids = dependency_graph.missing_uuids
        if missing_uuids:
            _logger.warning('The following UUIDs were found during dependency graph calculation but are not present '
                            'in the database: {}'.format(reduce(lambda a, b: a + ', ' + b, missing_uuids)))

        self.dependency_graph_widget.graph = dependency_graph.graph
        self.dependency_stack.set_visible_child(self.dependency_view)