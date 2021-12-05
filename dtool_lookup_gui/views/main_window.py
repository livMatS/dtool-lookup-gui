#
# Copyright 2020 Lars Pastewka, Johanns Hoermann
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
import traceback
import urllib.parse

from gi.repository import Gio, Gtk, GtkSource

import dtoolcore.utils
from dtool_info.utils import sizeof_fmt

from ..models.base_uris import all, LocalBaseURIModel
from ..models.datasets import DatasetModel
from ..utils.date import date_to_string
from .dataset_name_dialog import DatasetNameDialog
from .settings_dialog import SettingsDialog

_logger = logging.getLogger(__name__)


def _fill_manifest_tree_store(store, manifest, parent=None):
    nodes = {}

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

    edit_readme_switch = Gtk.Template.Child()
    save_metadata_button = Gtk.Template.Child()

    dependency_stack = Gtk.Template.Child()

    readme_source_view = Gtk.Template.Child()
    manifest_tree_view = Gtk.Template.Child()
    manifest_tree_store = Gtk.Template.Child()

    settings_button = Gtk.Template.Child()

    error_bar = Gtk.Template.Child()
    error_label = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_stack.set_visible_child(self.main_label)
        self.dataset_stack.set_visible_child(self.dataset_label)

        self.readme_buffer = self.readme_source_view.get_buffer()
        lang_manager = GtkSource.LanguageManager()
        self.readme_buffer.set_language(lang_manager.get_language("yaml"))
        self.readme_buffer.set_highlight_syntax(True)
        self.readme_buffer.set_highlight_matching_brackets(True)

        self.error_bar.hide()

    def refresh(self):
        asyncio.create_task(self.base_uri_list_box.refresh())

    @Gtk.Template.Callback()
    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    @Gtk.Template.Callback()
    def on_base_uri_selected(self, list_box, row):
        def update_base_uri_summary(datasets):
            total_size = sum([0 if dataset.size_int is None else dataset.size_int for dataset in datasets])
            row.info_label.set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')

        async def _select_base_uri():
            row.start_spinner()

            if hasattr(row, 'base_uri'):
                try:
                    datasets = await row.base_uri.all_datasets()
                    update_base_uri_summary(datasets)
                    if self.base_uri_list_box.get_selected_row() == row:
                        # Only update if the row is still selected
                        self.dataset_list_box.fill(datasets)
                except Exception as e:
                    self.show_error(e)
                self.create_dataset_button.set_sensitive(row.base_uri.scheme == 'file')
            elif hasattr(row, 'search_results'):
                # This is the search result
                if row.search_results is not None:
                    self.dataset_list_box.fill(row.search_results)
                    self.create_dataset_button.set_sensitive(False)

            self.main_stack.set_visible_child(self.main_paned)

            row.stop_spinner()
            row.task = None

        self.main_stack.set_visible_child(self.main_spinner)
        row = self.base_uri_list_box.get_selected_row()
        if row.task is None:
            row.task = asyncio.create_task(_select_base_uri())

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        def update_search_summary(datasets):
            row = self.base_uri_list_box.search_results_row
            total_size = sum([dataset.size_int for dataset in datasets])
            row.info_label.set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')

        async def fetch_search_results(keyword, on_show=None):
            row = self.base_uri_list_box.search_results_row
            row.start_spinner()
            try:
                datasets = await DatasetModel.search(keyword)
                datasets = datasets[:self._max_nb_datasets]  # Limit number of datasets that are shown
                row.search_results = datasets  # Cache datasets
                update_search_summary(datasets)
                if self.base_uri_list_box.get_selected_row() == row:
                    # Only update if the row is still selected
                    self.dataset_list_box.fill(datasets, on_show=on_show)
            except Exception as e:
                self.show_error(e)

            self.base_uri_list_box.select_search_results_row()
            self.main_stack.set_visible_child(self.main_paned)
            row.stop_spinner()

        self.main_stack.set_visible_child(self.main_spinner)
        row = self.base_uri_list_box.search_results_row
        row.search_results = None
        asyncio.create_task(fetch_search_results(self.search_entry.get_text()))

    @Gtk.Template.Callback()
    def on_dataset_selected(self, list_box, row):
        if row is not None:
            asyncio.create_task(self._update_dataset_view(row.dataset))
            self.dataset_stack.set_visible_child(self.dataset_box)

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

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            uri, = dialog.get_uris()
        elif response == Gtk.ResponseType.CANCEL:
            uri = None
        dialog.destroy()

        # Add directory to local inventory
        LocalBaseURIModel.add_directory(uri)

        # Refresh view of base URIs
        self.base_uri_list_box.refresh()

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

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            uris = dialog.get_uris()
            for uri in uris:
                self._add_item(uri)
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    @Gtk.Template.Callback()
    def on_edit_readme_state_set(self, widget, state):
        self.readme_source_view.set_editable(state)
        self.save_metadata_button.set_sensitive(state)
        if not state:
            # We need to save the metadata
            text = self.readme_buffer.get_text(self.readme_buffer.get_start_iter(),
                                               self.readme_buffer.get_end_iter(),
                                               False)
            self.dataset_list_box.get_selected_row().dataset.put_readme(text)

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
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            row.freeze()
            self.dataset_list_box.show_all()
            asyncio.create_task(self._update_dataset_view(self.dataset_list_box.get_selected_row().dataset))

    def on_copy_clicked(self, widget):
        self.dataset_list_box.get_selected_row().dataset.copy(widget.destination)

    def _add_item(self, uri):
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))
        handle = os.path.basename(fpath)
        handle = dtoolcore.utils.windows_to_unix_path(handle)  # NOQA
        self.dataset_list_box.get_selected_row().dataset.dataset.put_item(fpath, handle)

    def _create_dataset(self, name):
        base_uri = self.base_uri_list_box.get_selected_row()
        if base_uri is not None:
            self.dataset_list_box.add_dataset(base_uri.base_uri.create_dataset(name))
            self.dataset_list_box.show_all()

    async def _update_dataset_view(self, dataset):
        self.uuid_label.set_text(dataset.uuid)
        self.uri_label.set_text(dataset.uri)
        self.name_label.set_text(dataset.name)
        self.created_by_label.set_text(dataset.creator)
        self.frozen_at_label.set_text(dataset.date)
        self.size_label.set_text(dataset.size_str.strip())

        if dataset.scheme == 'file':
            self.show_button.set_sensitive(True)
            self.add_items_button.set_sensitive(not dataset.is_frozen)
            self.freeze_button.set_sensitive(not dataset.is_frozen)
            self.copy_button.set_sensitive(dataset.is_frozen)
        else:
            self.show_button.set_sensitive(False)
            self.add_items_button.set_sensitive(False)
            self.freeze_button.set_sensitive(False)
            self.copy_button.set_sensitive(True)

        async def _get_readme():
            self.readme_buffer.set_text(await dataset.get_readme())
        async def _get_manifest():
            _fill_manifest_tree_store(self.manifest_tree_store, await dataset.get_manifest())
        asyncio.create_task(_get_readme())
        asyncio.create_task(_get_manifest())

        #if dataset.has_dependencies:
        #    self.dependency_stack.show()
        #else:
        #    self.dependency_stack.hide()

        await self._update_copy_button(dataset)

    async def _update_copy_button(self, selected_dataset):
        destinations = []
        for base_uri in await all():
            if str(base_uri) != str(selected_dataset.base_uri):
                destinations += [str(base_uri)]
        self.copy_button.get_popover().update(destinations, self.on_copy_clicked)

    def show_error(self, exception):
        _logger.error(traceback.format_exc())
        self.error_label.set_text(str(exception))
        self.error_bar.show()
        self.error_bar.set_revealed(True)