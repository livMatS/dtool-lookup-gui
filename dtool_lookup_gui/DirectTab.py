#
# Copyright 2021 Johannes Hoermann, Lars Pastewka
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
import gi

import dtoolcore
from dtoolcore import DataSet

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

from . import date_to_string, _validate_readme

from . import (
    to_timestamp,
    date_to_string,
    datetime_to_string,
    fill_readme_tree_store,
    fill_manifest_tree_store)

from .models import (
    LocalBaseURIModel,
    DataSetListModel,
    DataSetModel,
    ProtoDataSetModel,
    MetadataSchemaListModel,
    UnsupportedTypeError,
    BaseURIModel,
)


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        # self.event_loop = event_loop
        self.builder = builder
        # self.settings = settings

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        self._selected_dataset = None
        self._selected_dataset_admin_metadata = None
        self._readme = None
        self._manifest = None

        self.readme_stack = self.builder.get_object('direct-readme-stack')
        self.manifest_stack = self.builder.get_object('direct-manifest-stack')

        self.base_uri_model = BaseURIModel()
        self.dataset_list_model = DataSetListModel()
        self.dataset_model = DataSetModel()

        self._base_uri = None

        # Configure the models.
        self.dataset_list_model.set_base_uri_model(self.base_uri_model)

    def on_base_uri_set(self,  filechooserbutton):
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        self._base_uri = filechooserbutton.get_uri()
        base_uri_entry_buffer.set_text(self._base_uri, -1)

    def on_base_uri_open(self,  button):
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        results_widget = self.builder.get_object('dtool-ls-results')
        statusbar_widget = self.builder.get_object('main-statusbar')

        # base_uri = filechooserbutton.get_filename()
        base_uri = base_uri_entry_buffer.get_text()
        self._base_uri = base_uri
        self.base_uri_model.put_base_uri(base_uri)

        self.dataset_list_model.reindex()
        self.refresh()
        # statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} datasets.')

        for entry in results_widget:
            entry.destroy()

        first_row = None

        dataset_list_columns = ("uuid", "name", "size_str", "num_items", "creator", "date", "uri")
        for props in self.dataset_list_model.yield_properties():
            values = [props[c] for c in dataset_list_columns]
            d = {c: v for c, v in zip(dataset_list_columns, values)}
            row = Gtk.ListBoxRow()
            if first_row is None:
                first_row = row
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{d["uuid"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{d["name"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(
                f'<small>Created by: {d["creator"]}, '
                f'frozen at: '
                f'{date_to_string(d["date"])}</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = d
            row.add(vbox)
            results_widget.add(row)
        results_widget.select_row(first_row)
        results_widget.show_all()

    def on_direct_dataset_selected(self, list_box, list_box_row):
        if list_box_row is None:
            return

        uri = list_box_row.dataset['uri']
        self._selected_dataset = DataSet.from_uri(uri)
        self._selected_dataset_admin_metadata = dtoolcore._admin_metadata_from_uri(uri, config_path=None)
        self._readme = None
        self._manifest = None

        self.builder.get_object('direct-dataset-name').set_text(
            self._selected_dataset.name)
        self.builder.get_object('direct-dataset-uuid').set_text(
            self._selected_dataset.uuid)
        self.builder.get_object('direct-dataset-uri').set_text(
            self._selected_dataset.uri)
        self.builder.get_object('direct-dataset-created-by').set_text(
            self._selected_dataset_admin_metadata['creator_username'])
        self.builder.get_object('direct-dataset-created-at').set_text(
            f'{datetime_to_string(self._selected_dataset_admin_metadata["created_at"])}')
        self.builder.get_object('direct-dataset-frozen-at').set_text(
            f'{datetime_to_string(self._selected_dataset_admin_metadata["frozen_at"])}')

        page = self.builder.get_object('direct-dataset-notebook').get_property('page')
        if page == 0:
            self._readme_task = asyncio.ensure_future(
                self._fetch_readme(self._selected_dataset.uri))
        elif page == 1:
            self._manifest_task = asyncio.ensure_future(
                self._fetch_manifest(self._selected_dataset.uri))

    async def _fetch_readme(self, uri):
        self.error_bar.set_revealed(False)
        self.readme_stack.set_visible_child(
            self.builder.get_object('direct-readme-spinner'))

        readme_view = self.builder.get_object('direct-dataset-readme')
        store = readme_view.get_model()
        store.clear()
        _readme_content = self._selected_dataset.get_readme_content()
        self._readme, error = _validate_readme(_readme_content)
        if error is not None:
            self.show_error(error)
            self._readme = _readme_content
        fill_readme_tree_store(store, self._readme)
        readme_view.columns_autosize()
        readme_view.show_all()

        self.readme_stack.set_visible_child(
            self.builder.get_object('direct-readme-view'))

    async def _fetch_manifest(self, uri):
        self.error_bar.set_revealed(False)
        self.manifest_stack.set_visible_child(
            self.builder.get_object('direct-manifest-spinner'))

        manifest_view = self.builder.get_object('direct-dataset-manifest')
        store = manifest_view.get_model()
        store.clear()
        self._manifest = self._selected_dataset._manifest
        try:
            fill_manifest_tree_store(store, self._manifest['items'])
        except Exception as e:
            print(e)
        manifest_view.columns_autosize()
        manifest_view.show_all()

        self.manifest_stack.set_visible_child(
            self.builder.get_object('direct-manifest-view'))

    def on_direct_dataset_view_switch_page(self, notebook, page, page_num):
        if self._selected_dataset is not None:
            if page_num == 0 and self._readme is None:
                self._readme_task = asyncio.ensure_future(
                    self._fetch_readme(self._selected_dataset.uri))
            elif page_num == 1 and self._manifest is None:
                self._manifest_task = asyncio.ensure_future(
                    self._fetch_manifest(self._selected_dataset.uri))

    def refresh(self):
        statusbar_widget = self.builder.get_object('main-statusbar')
        if self._base_uri is not None:
            statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} '
                                     f'datasets - {self._base_uri}')
        else:
            statusbar_widget.push(0, f'Specfy base URI.')

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)