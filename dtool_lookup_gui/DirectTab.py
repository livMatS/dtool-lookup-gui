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
# TODO: Make pure use of Tjelvar's model layer, move direct access to data sets
#       there
# TODO: Metadata input via GUI
# TODO: Copy dataset via GUI
import asyncio
import logging
import os.path
import urllib.parse

from gi.repository import Gtk, Gdk, Gio

from ruamel.yaml import YAML


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import dtoolcore

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
    DataSetModel,
    # MetadataSchemaListModel,
    UnsupportedTypeError,
)

HOME_DIR = os.path.expanduser("~")

# Page numbers inverted, very weird
DATASET_NOTEBOOK_README_PAGE = 0
DATASET_NOTEBOOK_MANIFEST_PAGE = 1

logger = logging.getLogger(__name__)


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
    def __init__(self, main_application, builder):
        self.main_application = main_application
        self.builder = builder

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        self._readme = None
        self._manifest = None

        self.readme_stack = self.builder.get_object('direct-readme-stack')
        self.manifest_stack = self.builder.get_object('direct-manifest-stack')

        self.base_uri_model = LocalBaseURIModel()
        self.dataset_list_model = DataSetListModel()
        self.dataset_model = DataSetModel()
        self.dataset_list_model.set_base_uri_model(self.base_uri_model)
        # print(self.base_uri_model.get_base_uri())
        # Configure the models.
        initial_base_uri = self.base_uri_model.get_base_uri()
        if initial_base_uri is None:
            initial_base_uri = HOME_DIR
        self._set_base_uri(initial_base_uri)
        self._list_datasets()

        try:
            self.dataset_list_model.set_active_index(0)
        except IndexError as exc:
            pass # Empty list, ignore

        dataset_uri = self.dataset_list_model.get_active_uri()
        # print(self.dataset_list_model.base_uri)
        if dataset_uri is not None:
            self._set_dataset_uri(dataset_uri)
            self._select_dataset(dataset_uri)
            self._show_dataset()

        self.refresh()

    # signal handles

    def on_base_uri_set(self,  filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
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
        self._mark_dataset_as_changed()
        self._list_datasets()
        self._show_dataset()
        self.refresh()

    def on_direct_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is None:
            return
        uri = list_box_row.dataset['uri']
        self._select_dataset(uri)
        self._mark_dataset_as_changed()
        self._show_dataset()
        self.refresh()

    def on_dtool_create(self, button):
        dialog = DatasetNameDialog(self.builder.get_object('main-window'))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            dataset_name = dialog.entry.get_text()
            self._create_dataset(dataset_name, self.base_uri_model.get_base_uri())
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    def on_dtool_item_add(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Add items", parent=self.builder.get_object('main-window'),
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

    def on_dtool_freeze(self, button):
        if not self.dataset_model.is_frozen:
            self.dataset_model.dataset.freeze()
            self._reload_dataset()
            self._mark_dataset_as_changed()
            self._list_datasets()
            self._show_dataset()
            self.refresh()
        else:
            self.show_error("Not a proto dataset.")

    def on_direct_dataset_view_switch_page(self, notebook, page, page_num):
        logger.debug(f"Selected page {page_num}.")
        self.refresh(page_num)

    def refresh(self, page=None):
        """Update statusbar and tab contents."""
        logger.debug("Refresh tab.")
        statusbar_widget = self.builder.get_object('main-statusbar')
        if not self.dataset_model.is_empty:
            statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} '
                                     f'datasets - {self.dataset_model.dataset.uri}')
        elif self.base_uri_model.get_base_uri() is not None:
            statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} '
                                     f'datasets - {self.base_uri_model.get_base_uri()}')
        else:
            statusbar_widget.push(0, f'Specify base URI.')

        dataset_notebook = self.builder.get_object('direct-dataset-notebook')
        if page is None:
            page = dataset_notebook.get_current_page()
        logger.debug(f"Selected page {page}.")

        if not self.dataset_model.is_empty:
            manifest_page = dataset_notebook.get_nth_page(DATASET_NOTEBOOK_MANIFEST_PAGE)

            if self.dataset_model.is_frozen:
                logger.debug("Show manifest tab.")
                manifest_page.show()
            else:
                logger.debug("Hide manifest tab.")
                manifest_page.hide()

            if page == DATASET_NOTEBOOK_README_PAGE:
                logger.debug("Show readme.")
                self._show_readme()
            elif page == DATASET_NOTEBOOK_MANIFEST_PAGE and self.dataset_model.is_frozen:
                logger.debug("Show manifest.")
                self._show_manifest()

    # private methods

    def _set_base_uri(self, uri):
        """Sets model base uri and associated file chooser and input field."""
        self.base_uri_model.put_base_uri(uri)
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        base_uri_entry_buffer.set_text(self.base_uri_model.get_base_uri(), -1)

        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            base_uri_file_chooser_button = self.builder.get_object('base-uri-chooser-button')
            base_uri_file_chooser_button.set_current_folder(fpath)

    def _set_dataset_uri(self, uri):
        """Set dataset file chooser and input field."""
        dataset_uri_entry_buffer = self.builder.get_object('dataset-uri-entry-buffer')
        dataset_uri_entry_buffer.set_text(uri, -1)

        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            dataset_uri_file_chooser_button = self.builder.get_object('dataset-uri-chooser-button')
            dataset_uri_file_chooser_button.set_current_folder(fpath)

    def _list_datasets(self, selected_uri=None):
        base_uri = self.base_uri_model.get_base_uri()
        if len(base_uri) == 0:
            self.show_error("Specify a non-empty base URI.")
            return

        results_widget = self.builder.get_object('dtool-ls-results')
        self.base_uri_model.put_base_uri(base_uri)

        try:
            self.dataset_list_model.reindex()
        except FileNotFoundError as exc:
            self.show_error(exc.__str__())
            return

        for entry in results_widget:
            entry.destroy()

        selected_row = None
        if selected_uri is None:
            if self.dataset_model.is_empty:
                selected_uri = self.dataset_list_model.get_active_uri()
            else:
                selected_uri = self.dataset_model.dataset.uri

        dataset_list_columns = ("uuid", "name", "size_str", "num_items", "creator", "date", "uri")
        proto_dataset_list_columns = ("uuid", "name", "creator", "uri")

        for props in self.dataset_list_model.yield_properties():
            # TODO: other way for distinguishing frozen and proto
            is_frozen = "date" in props

            if is_frozen:
                values = [props[c] for c in dataset_list_columns]
                d = {c: v for c, v in zip(dataset_list_columns, values)}
                prefix = ''
            else:
                values = [props[c] for c in proto_dataset_list_columns]
                d = {c: v for c, v in zip(proto_dataset_list_columns, values)}
                prefix = '*'


            row = Gtk.ListBoxRow()
            if selected_row is None or selected_uri == d["uri"]:
                # select the first row just in case the currently selected row is lost
                selected_row = row

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{prefix}<b>{d["uuid"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{d["name"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            if is_frozen:
                label.set_markup(
                    f'<small>Created by: {d["creator"]}, '
                    f'frozen at: '
                    f'{date_to_string(d["date"])}</small>')
            else:
                label.set_markup(
                    f'<small>Created by: {d["creator"]}, proto dataset</small>')
                vbox.pack_start(label, True, True, 0)
            row.dataset = d
            row.add(vbox)
            results_widget.add(row)

        results_widget.select_row(selected_row)
        results_widget.show_all()

    def _load_dataset(self, uri):
        """Load dataset and deal with UnsupportedTypeError exceptions."""
        try:
            self.dataset_model.load_dataset(uri)
            self.active_dataset_metadata_supported = True
        except UnsupportedTypeError:
            logger.warning("Dataset contains unsupported metadata type")
            self.active_dataset_metadata_supported = False

    def _reload_dataset(self):
        self._load_dataset(self.dataset_model.dataset.uri)

    def _mark_dataset_as_changed(self):
        """Mark a change in the dataset, reload content where necessary."""
        self._reload_readme = True
        self._reload_manifest = True

    def _select_dataset(self, uri):
        """Specify dataset selected in list."""
        if len(uri) > 0:
            self.dataset_list_model.set_active_index_by_uri(uri)
            self._load_dataset(uri)
            self._mark_dataset_as_changed()
        else:
            self.show_error("Specify a non-empty dataset URI.")
            return

    def _show_dataset(self):
        """Display dataset info."""
        # TODO: use self.dataset_model.metadata_model instead of direct README content
        ds = self.dataset_model.dataset

        uri = self.dataset_list_model.get_active_uri()
        # TODO: move admin metadata into DataSetModel
        admin_metadata = dtoolcore._admin_metadata_from_uri(uri, config_path=None)
        self._readme = None
        self._manifest = None

        self.builder.get_object('direct-dataset-name').set_text(ds.name)
        self.builder.get_object('direct-dataset-uuid').set_text(ds.uuid)
        self.builder.get_object('direct-dataset-uri').set_text(ds.uri)
        self.builder.get_object('direct-dataset-created-by').set_text(
            admin_metadata['creator_username'])
        self.builder.get_object('direct-dataset-created-at').set_text(
            f'{datetime_to_string(admin_metadata["created_at"])}')
        if self.dataset_model.is_frozen:
            self.builder.get_object('direct-dataset-frozen-at').set_text(
                f'{datetime_to_string(admin_metadata["frozen_at"])}')
        else:
            self.builder.get_object('direct-dataset-frozen-at').set_text("-")

        self.refresh()

    def _show_readme(self):
        if self._reload_readme:
            logger.debug("Reload readme.")
            self._readme_task = asyncio.ensure_future(
                self._fetch_readme(self.dataset_model.dataset.uri))
        else:
            logger.debug("Readme cached, don't reload.")
        self._reload_readme = False

    def _show_manifest(self):
        if self._reload_manifest:
            logger.debug("Reload manifest.")
            self._manifest_task = asyncio.ensure_future(
                self._fetch_manifest(self.dataset_model.dataset.uri))
        else:
            logger.debug("Manifest cached, don't reload.")
        self._reload_manifest = False

    async def _fetch_readme(self, uri):
        self.error_bar.set_revealed(False)
        self.readme_stack.set_visible_child(
            self.builder.get_object('direct-readme-spinner'))

        readme_view = self.builder.get_object('direct-dataset-readme')
        store = readme_view.get_model()
        store.clear()
        _readme_content = self.dataset_model.dataset.get_readme_content()
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
        # TODO: access via unprotected method
        self._manifest = self.dataset_model.dataset._manifest
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

        # TODO: move creation without metadata and items into model layer
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
                self.show_error("Need to specify symlink path. NOT IMPLEMENTED.")

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
        self._load_dataset(proto_dataset.uri)
        self._initialize_readme()
        self._mark_dataset_as_changed()
        self._list_datasets()
        self._show_dataset()

    def _initialize_readme(self, readme_template_path=None):
        """Fill README.yml with template configured in dtool.json config."""
        readme_template = _get_readme_template(readme_template_path)
        yaml = YAML()
        yaml.explicit_start = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        descriptive_metadata = yaml.load(readme_template)
        stream = StringIO()
        yaml.dump(descriptive_metadata, stream)
        self.dataset_model.dataset.put_readme(stream.getvalue())

    def _add_item(self, uri):
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))
        handle = os.path.basename(fpath)
        handle = dtoolcore.utils.windows_to_unix_path(handle)  # NOQA
        self.dataset_model.dataset.put_item(fpath, handle)

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)