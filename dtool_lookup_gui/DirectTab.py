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
# TODO: date not shown correctly in local results
# TODO: status bar not updated correctly
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

from . import (
    GlobalConfig,
    datetime_to_string,
    fill_readme_tree_store,
    fill_manifest_tree_store,
    _validate_readme)

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
    def __init__(self, parent):
        self.main_application = parent.main_application
        self.builder = parent.builder

        self._readme = None
        self._manifest = None

        self._reload_readme = True
        self._reload_manifest = True

        # gui elements
        self.base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        self.base_uri_entry_buffer = self.builder.get_object('lhs-base-uri-entry-buffer')
        self.base_uri_file_chooser_button = self.builder.get_object('base-uri-chooser-button')
        self.dataset_list_auto_refresh = self.builder.get_object('direct-dataset-list-auto-refresh')
        self.dataset_manifest = self.builder.get_object('direct-dataset-manifest')
        self.dataset_notebook = self.builder.get_object('direct-dataset-notebook')
        self.dataset_readme = self.builder.get_object('direct-dataset-readme')
        self.dataset_uri_entry_buffer = self.builder.get_object('lhs-dataset-uri-entry-buffer')
        self.dataset_uri_file_chooser_button = self.builder.get_object('dataset-uri-chooser-button')
        self.dtool_add_items_button = self.builder.get_object('dtool-add-items')
        self.dtool_dataset_list = self.builder.get_object('dtool-ls-results')
        self.dtool_freeze_button = self.builder.get_object('dtool-freeze')
        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')
        self.main_window = self.builder.get_object('main-window')
        self.manifest_spinner =  self.builder.get_object('direct-manifest-spinner')
        self.manifest_stack = self.builder.get_object('direct-manifest-stack')
        self.manifest_view = self.builder.get_object('direct-manifest-view')
        self.readme_spinner = self.builder.get_object('direct-readme-spinner')
        self.readme_stack = self.builder.get_object('direct-readme-stack')
        self.readme_view = self.builder.get_object('direct-readme-view')
        self.statusbar_widget = self.builder.get_object('main-statusbar')

        # models
        # self.dataset_model = parent.lhs_dataset_model
        self.lhs_base_uri_inventory_group = parent.lhs_base_uri_inventory_group
        self.lhs_base_uri_inventory_group.append_dataset_list_box(self.dtool_dataset_list)

        self.lhs_base_uri_inventory_group.base_uri_selector.append_file_chooser_button(
            self.base_uri_file_chooser_button)

        self.lhs_base_uri_inventory_group.dataset_uri_selector.append_file_chooser_button(
            self.dataset_uri_file_chooser_button)

        # configure
        self.dataset_list_auto_refresh.set_active(GlobalConfig.auto_refresh_on)
        # self.dtool_dataset_list.auto_refresh = GlobalConfig.auto_refresh_on

        dataset_uri = self.lhs_base_uri_inventory_group.get_selected_uri()
        # print(self.dataset_list_model.base_uri)
        if dataset_uri is not None:
          self._show_dataset()

        # self.refresh()

    # signal handles

    def on_lhs_dataset_uri_open(self,  button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self._mark_dataset_as_changed()
        self._show_dataset()
        self.refresh()

    def on_lhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is None:
            return
        self._mark_dataset_as_changed()
        self._show_dataset()
        self.refresh()

    def on_dtool_create(self, button):
        dialog = DatasetNameDialog(self.main_window)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            dataset_name = dialog.entry.get_text()
            self._create_dataset(dataset_name, self.lhs_base_uri_inventory_group.base_uri)

        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    def on_dtool_item_add(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Add items", parent=self.main_window,
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
        if not self.lhs_base_uri_inventory_group.dataset_model.is_frozen:
            self.lhs_base_uri_inventory_group.dataset_model.dataset.freeze()
            self.lhs_base_uri_inventory_group.apply_dataset_uri()  # reloads dataset
            self.lhs_base_uri_inventory_group.refresh()  # rebuilds list
            self._mark_dataset_as_changed()
            self._show_dataset()
            self.refresh()
        else:
            self.show_error("Not a proto dataset.")

    def on_direct_dataset_view_switch_page(self, notebook, page, page_num):
        logger.debug(f"Selected page {page_num}.")
        self.refresh(page_num)

    def refresh(self, page=None):
        """Update statusbar and tab contents."""
        if not self._sensitive:
            return

        logger.debug("Refresh tab.")
        if not self.lhs_base_uri_inventory_group.dataset_model.is_empty:
            self.statusbar_widget.push(0, f'{len(self.lhs_base_uri_inventory_group.dataset_list_model._datasets)} '
                                     f'datasets - {self.lhs_base_uri_inventory_group.dataset_model.dataset.uri}')
        elif self.lhs_base_uri_inventory_group.dataset_list_model.base_uri is not None:
            self.statusbar_widget.push(0, f'{len(self.lhs_base_uri_inventory_group.dataset_list_model._datasets)} '
                                     f'datasets - {self.lhs_base_uri_inventory_group.dataset_list_model.base_uri}')
        else:
            self.statusbar_widget.push(0, f'Specify base URI.')

        if page is None:
            page = self.dataset_notebook.get_current_page()
        logger.debug(f"Selected page {page}.")

        if not self.lhs_base_uri_inventory_group.dataset_model.is_empty:
            manifest_page = self.dataset_notebook.get_nth_page(DATASET_NOTEBOOK_MANIFEST_PAGE)

            if self.lhs_base_uri_inventory_group.dataset_model.is_frozen:
                logger.debug("Showing frozen dataset.")
                manifest_page.show()
                self.dtool_freeze_button.set_sensitive(False)
                self.dtool_add_items_button.set_sensitive(False)
            else:
                logger.debug("Showing proto dataset.")
                manifest_page.hide()
                self.dtool_freeze_button.set_sensitive(True)
                self.dtool_add_items_button.set_sensitive(True)

            if page == DATASET_NOTEBOOK_README_PAGE:
                logger.debug("Show readme.")
                self._show_readme()
            elif page == DATASET_NOTEBOOK_MANIFEST_PAGE and self.lhs_base_uri_inventory_group.dataset_model.is_frozen:
                logger.debug("Show manifest.")
                self._show_manifest()

    # private methods
    def _mark_dataset_as_changed(self):
        """Mark a change in the dataset, reload content where necessary."""
        self._reload_readme = True
        self._reload_manifest = True

    def _show_dataset(self):
        """Display dataset info."""
        # TODO: use self.dataset_model.metadata_model instead of direct README content
        ds = self.lhs_base_uri_inventory_group.dataset_model.dataset
        uri = self.lhs_base_uri_inventory_group.get_selected_uri()
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
        if self.lhs_base_uri_inventory_group.dataset_model.is_frozen:
            self.builder.get_object('direct-dataset-frozen-at').set_text(
                f'{datetime_to_string(admin_metadata["frozen_at"])}')
        else:
            self.builder.get_object('direct-dataset-frozen-at').set_text("-")

    def _show_readme(self):
        if self._reload_readme:
            logger.debug("Reload readme.")
            self._readme_task = asyncio.ensure_future(
                self._fetch_readme(self.lhs_base_uri_inventory_group.dataset_model.dataset.uri))
        else:
            logger.debug("Readme cached, don't reload.")
        self._reload_readme = False

    def _show_manifest(self):
        if self._reload_manifest:
            logger.debug("Reload manifest.")
            self._manifest_task = asyncio.ensure_future(
                self._fetch_manifest(self.lhs_base_uri_inventory_group.dataset_model.dataset.uri))
        else:
            logger.debug("Manifest cached, don't reload.")
        self._reload_manifest = False

    async def _fetch_readme(self, uri):
        self.error_bar.set_revealed(False)
        self.readme_stack.set_visible_child(self.readme_spinner)

        store = self.dataset_readme.get_model()
        store.clear()
        _readme_content = self.lhs_base_uri_inventory_group.dataset_model.dataset.get_readme_content()
        self._readme, error = _validate_readme(_readme_content)
        if error is not None:
            self.show_error(error)
            self._readme = _readme_content
        fill_readme_tree_store(store, self._readme)
        self.dataset_readme.columns_autosize()
        self.dataset_readme.show_all()

        self.readme_stack.set_visible_child(self.readme_view)

    async def _fetch_manifest(self, uri):
        self.error_bar.set_revealed(False)
        self.manifest_stack.set_visible_child(self.manifest_spinner)

        manifest_view = self.dataset_manifest
        store = manifest_view.get_model()
        store.clear()
        # TODO: access via unprotected method
        self._manifest = self.lhs_base_uri_inventory_group.dataset_model.dataset._manifest
        try:
            fill_manifest_tree_store(store, self._manifest['items'])
        except Exception as e:
            print(e)
        manifest_view.columns_autosize()
        manifest_view.show_all()

        self.manifest_stack.set_visible_child(self.manifest_view)

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
        self.lhs_base_uri_inventory_group.dataset_model.load_dataset(proto_dataset.uri)
        self._initialize_readme()
        self._mark_dataset_as_changed()
        self.lhs_base_uri_inventory_group.refresh(selected_uri=proto_dataset.uri)
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
        self.lhs_base_uri_inventory_group.dataset_model.dataset.put_readme(stream.getvalue())

    # TODO: allow adding whole folders
    def _add_item(self, uri):
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))
        handle = os.path.basename(fpath)
        handle = dtoolcore.utils.windows_to_unix_path(handle)  # NOQA
        self.lhs_base_uri_inventory_group.dataset_model.dataset.put_item(fpath, handle)

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def set_sensitive(self, sensitive=True):
        self._sensitive = sensitive