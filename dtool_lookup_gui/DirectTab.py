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
import datetime
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

import os.path

from ruamel.yaml import YAML

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import dtoolcore
from dtoolcore import DataSet, ProtoDataSet

from dtool_create.dataset import _get_readme_template

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
    ProtoDataSetListModel,
    DataSetModel,
    ProtoDataSetModel,
    MetadataSchemaListModel,
    UnsupportedTypeError,
    BaseURIModel,
)

DATASET_NOTEBOOK_README_PAGE = 0
DATASET_NOTEBOOK_MANIFEST_PAGE = 1

class DatasetNameDialog(Gtk.Dialog):
    def __init__(self, parent, default_name=''):
        super().__init__(title="Specify dataset name", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, -1)

        label = Gtk.Label(label="name:")
        self.entry = Gtk.Entry()
        self.entry.set_text(default_name)
        box = self.get_content_area()
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        box.add(hbox)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entry, True, True, 0)
        self.show_all()


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

        self.base_uri_model = LocalBaseURIModel()
        self.proto_dataset_list_model = ProtoDataSetListModel()
        self.dataset_list_model = DataSetListModel()
        self.dataset_model = DataSetModel()

        self._set_base_uri(self.base_uri_model.get_base_uri())
        self._dataset_uri = None

        # Configure the models.
        self.proto_dataset_list_model.set_base_uri_model(self.base_uri_model)
        self.dataset_list_model.set_base_uri_model(self.base_uri_model)

        self._list_datasets()
        self.refresh()

    # signal handles

    def on_base_uri_set(self,  filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
        # self.base_uri_model.set_base_uri(base_uri)
        self._set_base_uri(base_uri)

    def on_base_uri_open(self,  button):
        """Open base URI button clicked."""
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        base_uri = base_uri_entry_buffer.get_text()
        self.base_uri_model.put_base_uri(base_uri)
        self._list_datasets()

    def on_dataset_uri_set(self,  filechooserbutton):
        self._set_dataset_uri(filechooserbutton.get_uri())

    def on_dataset_uri_open(self,  button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        dataset_uri_entry_buffer = self.builder.get_object('dataset-uri-entry-buffer')
        uri = dataset_uri_entry_buffer.get_text()
        self._select_dataset(uri)

    def on_direct_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is None:
            return
        uri = list_box_row.dataset['uri']
        self._select_dataset(uri)

    def on_dtool_create(self, button):
        dialog = DatasetNameDialog(self.builder.get_object('main-window'))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            dataset_name = dialog.entry.get_text()
            self._create_dataset(dataset_name, self.base_uri_model.get_base_uri())
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()
        self._list_datasets()
        self.refresh(force_readme_refresh=True)

    def on_dtool_freeze(self, button):
        if isinstance(self._selected_dataset, ProtoDataSet):
            self._selected_dataset.freeze()
            self._list_datasets()
            #self._set_selected_dataset_row_by_uri(self._selected_dataset.uri)
            self.refresh(force_readme_refresh=True, force_manifest_refresh=True)
        else:
            self.show_error("Not a proto dataset.")

    def refresh(self, force_readme_refresh=False, force_manifest_refresh=False):
        """Update statusbar and tab contents."""
        statusbar_widget = self.builder.get_object('main-statusbar')
        if self._dataset_uri is not None:
            statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} '
                                     f'datasets - {self._dataset_uri}')
        elif self.base_uri_model.get_base_uri() is not None:
            statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} '
                                     f'datasets - {self.base_uri_model.get_base_uri()}')
        else:
            statusbar_widget.push(0, f'Specify base URI.')

        dataset_notebook = self.builder.get_object('direct-dataset-notebook')
        manifest_page = dataset_notebook.get_nth_page(DATASET_NOTEBOOK_MANIFEST_PAGE)
        page = dataset_notebook.get_property('page')

        if self._selected_dataset is not None:
            if self._readme is None:
                force_readme_refresh = True

            if isinstance(self._selected_dataset, ProtoDataSet):
                manifest_page.hide()
            else:
                manifest_page.show()
                if self._manifest is None:
                    force_manifest_refresh = True

            if page == DATASET_NOTEBOOK_README_PAGE and force_readme_refresh:
                self._readme_task = asyncio.ensure_future(
                    self._fetch_readme(self._selected_dataset.uri))
            elif page == DATASET_NOTEBOOK_MANIFEST_PAGE and force_manifest_refresh and not isinstance(self._selected_dataset, ProtoDataSet):
                self._manifest_task = asyncio.ensure_future(
                    self._fetch_manifest(self._selected_dataset.uri))

    # private methods

    def _set_base_uri(self, uri):
        """Sets model base uri and associated file chooser and input field."""
        self.base_uri_model.put_base_uri(uri)
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        base_uri_entry_buffer.set_text(self.base_uri_model.get_base_uri(), -1)

        if os.path.isdir(uri):
            abspath = os.path.abspath(uri)
            base_uri_file_chooser_button = self.builder.get_object('base-uri-chooser-button')
            base_uri_file_chooser_button.set_current_folder(abspath)

    def _set_dataset_uri(self, uri):
        """Sets state variable _dataset_uri as well as the associated file chooser and input field."""
        self._dataset_uri = uri
        dataset_uri_entry_buffer = self.builder.get_object('dataset-uri-entry-buffer')
        dataset_uri_entry_buffer.set_text(self._dataset_uri, -1)

        if os.path.isdir(uri):
            abspath = os.path.abspath(uri)
            dataset_uri_file_chooser_button = self.builder.get_object('dataset-uri-chooser-button')
            dataset_uri_file_chooser_button.set_current_folder(abspath)

    def _list_datasets(self):
        base_uri = self.base_uri_model.get_base_uri()
        if len(base_uri) == 0:
            self.show_error("Specify a non-empty base URI.")
            return

        results_widget = self.builder.get_object('dtool-ls-results')
        self.base_uri_model.put_base_uri(base_uri)

        try:
            self.proto_dataset_list_model.reindex()
        except FileNotFoundError as exc:
            self.show_error(exc.__str__())
            return

        try:
            self.dataset_list_model.reindex()
        except FileNotFoundError as exc:
            self.show_error(exc.__str__())
            return

        self._set_base_uri(base_uri)

        self.refresh()

        for entry in results_widget:
            entry.destroy()

        first_row = None

        proto_dataset_list_columns = ("uuid", "name", "creator", "uri")
        for props in self.proto_dataset_list_model.yield_properties():
            values = [props[c] for c in proto_dataset_list_columns]
            d = {c: v for c, v in zip(proto_dataset_list_columns, values)}
            row = Gtk.ListBoxRow()
            if first_row is None:
                first_row = row
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'*<b>{d["uuid"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{d["name"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(
                f'<small>Created by: {d["creator"]}, proto dataset</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = d
            row.add(vbox)
            results_widget.add(row)

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

    # def _get_dataset_row(self, uri):
    #     dataset_list_box = self.builder.get_object('dtool-ls-results')
    #     for row in dataset_list_box.row:
    #         if row.dataset.uri == uri:
    #             return row
    #     return None
    #
    # def _set_selected_dataset_row(self, row):
    #     dataset_list_box = self.builder.get_object('dtool-ls-results')
    #     dataset_list_box.select_row(row)
    #
    # def _set_selected_dataset_row_by_uri(self, uri):
    #     row = self._get_dataset_row(uri)
    #     self._set_selected_dataset_row(row)


    def _select_dataset(self, uri):
        """Selects dataset at URI and displays info."""

        if len(uri) > 0:
            self._set_dataset_uri(uri)
        else:
            self.show_error("Specify a non-empty dataset URI.")
            return

        # determine whether this is a proto dataset first
        try:
            admin_metadata = dtoolcore._admin_metadata_from_uri(uri, None)
        except (dtoolcore.DtoolCoreTypeError, FileNotFoundError) as exc:
            self.show_error(exc.__str__())
            return

        try:
            if admin_metadata["type"] == "protodataset":
                self._selected_dataset = ProtoDataSet.from_uri(uri)
            else:
                self._selected_dataset = DataSet.from_uri(uri)
        except dtoolcore.DtoolCoreTypeError as exc:
            self.show_error(exc.__str__())
            return

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
        if isinstance(self._selected_dataset, ProtoDataSet):
            self.builder.get_object('direct-dataset-frozen-at').set_text("-")
        else:
            self.builder.get_object('direct-dataset-frozen-at').set_text(
                f'{datetime_to_string(self._selected_dataset_admin_metadata["frozen_at"])}')

        #self._set_selected_dataset_row_by_uri(uri)
        self.refresh()

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

    def _create_dataset(self, name, base_uri, symlink_path=None):
        """Create a proto dataset."""
        # As in https://github.com/jic-dtool/dtool-create/blob/master/dtool_create/dataset.py#L133

        if not dtoolcore.utils.name_is_valid(name):
            valid_chars = " ".join(dtoolcore.utils.NAME_VALID_CHARS_LIST)
            self.show_error(f"Invalid dataset name '{name}'. "
                            f"Name must be 80 characters or less. "
                            f"Dataset names may only contain the characters: {valid_chars}")
            return

        admin_metadata = dtoolcore.generate_admin_metadata(name)
        parsed_base_uri = dtoolcore.utils.generous_parse_uri(base_uri)

        if parsed_base_uri.scheme == "symlink":
            if symlink_path is None:
                raise click.UsageError("Need to specify symlink path using the -s/--symlink-path option")  # NOQA

        if symlink_path:
            base_uri = dtoolcore.utils.sanitise_uri(
                "symlink:" + parsed_base_uri.path
            )
            parsed_base_uri = dtoolcore.utils.generous_parse_uri(base_uri)

        # Create the dataset.
        proto_dataset = dtoolcore.generate_proto_dataset(
            admin_metadata=admin_metadata,
            base_uri=dtoolcore.utils.urlunparse(parsed_base_uri),
            config_path=None)

        # If we are creating a symlink dataset we need to set the symlink_path
        # attribute on the storage broker.
        if symlink_path:
            symlink_abspath = os.path.abspath(symlink_path)
            proto_dataset._storage_broker.symlink_path = symlink_abspath
        try:
            proto_dataset.create()
        except dtoolcore.storagebroker.StorageBrokerOSError as err:
            self.show_error(err.__str__)

        # Initialize with empty README.yml
        proto_dataset.put_readme("")
        self._select_dataset(proto_dataset.uri)
        self._initialize_readme()

    def _initialize_readme(self, readme_template_path=None):
        readme_template = _get_readme_template(readme_template_path)
        yaml = YAML()
        yaml.explicit_start = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        descriptive_metadata = yaml.load(readme_template)
        stream = StringIO()
        yaml.dump(descriptive_metadata, stream)
        self._selected_dataset.put_readme(stream.getvalue())

    def on_direct_dataset_view_switch_page(self, notebook, page, page_num):
        self.refresh()

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)