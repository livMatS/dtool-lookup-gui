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
import urllib.parse

from gi.repository import Gio, Gtk, GtkSource

import dtoolcore.utils
from dtool_info.utils import sizeof_fmt

from ..models.base_uris import LocalBaseURIModel
from ..utils.date import date_to_string
from .dataset_name_dialog import DatasetNameDialog
from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


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

    create_dataset_button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    search_entry = Gtk.Template.Child()

    base_uri_list_box = Gtk.Template.Child()
    dataset_list_box = Gtk.Template.Child()

    uuid_label = Gtk.Template.Child()
    uri_label = Gtk.Template.Child()
    name_label = Gtk.Template.Child()
    created_by_label = Gtk.Template.Child()
    frozen_at_label = Gtk.Template.Child()
    size_label = Gtk.Template.Child()

    show_button = Gtk.Template.Child()
    add_items_button = Gtk.Template.Child()
    freeze_button = Gtk.Template.Child()
    transfer_button = Gtk.Template.Child()

    dependency_stack = Gtk.Template.Child()

    readme_source_view = Gtk.Template.Child()
    manifest_tree_view = Gtk.Template.Child()
    manifest_tree_store = Gtk.Template.Child()

    settings_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.readme_buffer = self.readme_source_view.get_buffer()
        lang_manager = GtkSource.LanguageManager()
        self.readme_buffer.set_language(lang_manager.get_language("yaml"))
        self.readme_buffer.set_highlight_syntax(True)
        self.readme_buffer.set_highlight_matching_brackets(True)

    @Gtk.Template.Callback()
    def on_window_show(self, widget):
        self.base_uri_list_box.refresh()

    @Gtk.Template.Callback()
    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    @Gtk.Template.Callback()
    def on_base_uri_selected(self, list_box, row):
        def update_base_uri_summary(datasets):
            total_size = sum([0 if dataset.size_int is None else dataset.size_int for dataset in datasets])
            row.info_label.set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')
        if hasattr(row, 'base_uri'):
            self.dataset_list_box.from_base_uri(row.base_uri, on_show=update_base_uri_summary)
            self.create_dataset_button.set_sensitive(row.base_uri.scheme == 'file')
        elif hasattr(row, 'search_results'):
            # This is the search result
            self.dataset_list_box.fill(row.search_results)
            self.create_dataset_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_dataset_selected(self, list_box, row):
        if row is not None:
            self._update_dataset_view(row.dataset)

    @Gtk.Template.Callback()
    def on_search_activate(self, widget):
        def update_search_summary(datasets):
            total_size = sum([dataset.size_int for dataset in datasets])
            self.base_uri_list_box.search_results_row.search_results = datasets
            self.base_uri_list_box.search_results_row.info_label \
                .set_text(f'{len(datasets)} datasets, {sizeof_fmt(total_size).strip()}')
        self.base_uri_list_box.select_search_results_row()
        self.dataset_list_box.search(self.search_entry.get_text(), on_show=update_search_summary)

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

    def _update_dataset_view(self, dataset):
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
            self.transfer_button.set_label('Upload')
        else:
            self.show_button.set_sensitive(False)
            self.add_items_button.set_sensitive(False)
            self.freeze_button.set_sensitive(False)
            self.transfer_button.set_label('Download')

        if dataset.has_dependencies:
            self.dependency_stack.show()
        else:
            self.dependency_stack.hide()

        self._update_readme(dataset)
        self._update_manifest(dataset)

    def _update_readme(self, dataset):
        async def _fetch_readme(dataset):
            readme = await dataset.readme()
            self.readme_buffer.set_text(readme)
        asyncio.create_task(_fetch_readme(dataset))

    def _update_manifest(self, dataset):
        async def _fetch_manifest(dataset):
            self.manifest_tree_store.clear()
            manifest = await dataset.manifest()
            _fill_manifest_tree_store(self.manifest_tree_store, manifest)
        asyncio.create_task(_fetch_manifest(dataset))
