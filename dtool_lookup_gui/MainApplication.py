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
import concurrent.futures
import logging
import os

from dtool_lookup_api.core.config import Config
Config.interactive = False

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

import gbulb
gbulb.install(gtk=True)

from .models import (
    LocalBaseURIModel,
    RemoteBaseURIModel,
    DataSetListModel,
    DataSetModel,
)

from .dtool_gtk import BaseURISelector, DatasetURISelector, BaseURIInventoryGroup
from . import GlobalConfig, LookupTab, DirectTab, TransferTab, SettingsDialog
from . import GlobalConfig, LookupTab, DirectTab, TransferTab
from .views.settings_dialog import SettingsDialog
from .views.metadata_editor import MetadataEditor

logger = logging.getLogger(__name__)

HOME_DIR = os.path.expanduser("~")

LOOKUP_TAB = 0
DIRECT_TAB = 1
TRANSFER_TAB = 2

# used for wrapping a list of signal handlers
# source: https://github.com/LinuxCNC/linuxcnc/blob/master/src/emc/usr_intf/gscreen/gscreen.py
class Trampoline(object):
    def __init__(self, methods):
        self.methods = methods

    def __call__(self, *args, **kwargs):
        retval = None
        for m in self.methods:
            new_retval = m(*args, **kwargs)
            if new_retval is not None and retval is not None:
                raise RuntimeError('Can only trampoline signals that do not return anything')
            else:
                retval = new_retval
        return retval

    def append(self, method):
        self.methods.append(method)


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.dirname(__file__), Gio.SettingsSchemaSource.get_default(),
            False)
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-lookup-gui", False)
        self.settings = Gio.Settings.new_full(schema, None, None)
        self.config = Config

    @property
    def dependency_keys(self):
        return self.settings.get_string('dependency-keys')


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        self.main_application = self
        self.event_loop = event_loop
        self.builder = builder
        self.settings = settings

        # gui elements
        self.lhs_base_uri_entry_buffer = self.builder.get_object('lhs-base-uri-entry-buffer')
        self.lhs_dataset_uri_entry_buffer = self.builder.get_object('lhs-dataset-uri-entry-buffer')
        self.rhs_base_uri_entry_buffer = self.builder.get_object('rhs-base-uri-entry-buffer')
        self.rhs_dataset_uri_entry_buffer = self.builder.get_object('rhs-dataset-uri-entry-buffer')

        self.main_window = self.builder.get_object('main-window')
        self.metadata_dialog = self.builder.get_object('metadata-dialog')
        self.settings_window = self.builder.get_object('settings-window')
        self.main_notebook = self.builder.get_object('main-notebook')

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        # models
        self.lhs_dataset_list_model = DataSetListModel()
        self.lhs_base_uri_model = LocalBaseURIModel()
        self.lhs_dataset_model = DataSetModel()
        self.lhs_dataset_list_model.set_base_uri_model(self.lhs_base_uri_model)

        self.rhs_dataset_list_model = DataSetListModel()
        self.rhs_base_uri_model = RemoteBaseURIModel()
        self.rhs_dataset_model = DataSetModel()  # dummy, not used
        self.rhs_dataset_list_model.set_base_uri_model(self.rhs_base_uri_model)

        self.lhs_base_uri_selector = BaseURISelector(base_uri_model=self.lhs_base_uri_model,
                                                     text_entry_buffer=self.lhs_base_uri_entry_buffer)
        self.rhs_base_uri_selector = BaseURISelector(base_uri_model=self.rhs_base_uri_model,
                                                     text_entry_buffer=self.rhs_base_uri_entry_buffer)
        self.lhs_dataset_uri_selector = DatasetURISelector(dataset_model=self.lhs_dataset_model,
                                                        text_entry_buffer=self.lhs_dataset_uri_entry_buffer)
        self.rhs_dataset_uri_selector = DatasetURISelector(dataset_model=self.rhs_dataset_model,
                                                        text_entry_buffer=self.rhs_dataset_uri_entry_buffer)
        self.lhs_base_uri_inventory_group = BaseURIInventoryGroup(base_uri_selector=self.lhs_base_uri_selector,
                                                                  dataset_uri_selector=self.lhs_dataset_uri_selector,
                                                                  dataset_list_model=self.lhs_dataset_list_model)
        self.rhs_base_uri_inventory_group = BaseURIInventoryGroup(base_uri_selector=self.rhs_base_uri_selector,
                                                                  dataset_uri_selector=self.rhs_dataset_uri_selector,
                                                                  dataset_list_model=self.rhs_dataset_list_model)


        #configure
        self.lhs_base_uri_inventory_group.set_error_callback(self.show_error)
        self.rhs_base_uri_inventory_group.set_error_callback(self.show_error)

        self.lhs_base_uri_inventory_group.set_auto_refresh(GlobalConfig.auto_refresh_on)
        self.rhs_base_uri_inventory_group.set_auto_refresh(False)

        self.error_bar.set_revealed(False)

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.lookup_tab = LookupTab.SignalHandler(self)
        self.direct_tab = DirectTab.SignalHandler(self)
        self.transfer_tab = TransferTab.SignalHandler(self)
        # self.settings_dialog = SettingsDialog.SignalHandler(self)
        self.metadata_editor = MetadataEditor.SignalHandler(self)

        self.rhs_base_uri_inventory_group.refresh()
        self.lhs_base_uri_inventory_group.refresh()

        # Create a dictionary to hold the signal-handler pairs
        self.handlers = {}

        # load all signal handlers into sel.handlers
        self._load_handlers(self)
        self._load_handlers(self.lookup_tab)
        self._load_handlers(self.direct_tab)
        self._load_handlers(self.transfer_tab)
        self._load_handlers(self.metadata_editor)
        self._load_handlers(self)

        self.builder.connect_signals(self.handlers)
        self.main_window.show_all()

        self.refresh()

    def _load_handlers(self, object):
        """Scan object for signal handlers and add them to a (class-global) """
        if isinstance(object, dict):
            methods = object.items()
        else:
            methods = map(lambda n: (n, getattr(object, n, None)), dir(object))

        for method_name, method in methods:
            if method_name.startswith('_'):
                continue
            if callable(method):
                if method_name in self.handlers:
                    logger.debug("Registering additional callback for '%s'" % (method_name))
                    self.handlers[method_name].append(method)
                else:
                    logger.debug("Registering callback for '%s'" % (method_name))
                    self.handlers[method_name] = Trampoline([method])

    # signal handlers

    def on_lhs_base_uri_set(self, file_chooser_button):
        """Base URI directory selected with file chooser."""
        base_uri = file_chooser_button.get_uri()
        logger.debug(f"Selected lhs base URI '{base_uri}' via file chooser.")
        self.lhs_base_uri_inventory_group.set_base_uri_from_file_chooser_button(file_chooser_button)

    def on_rhs_base_uri_set(self, file_chooser_button):
        """Base URI directory selected with file chooser."""
        base_uri = file_chooser_button.get_uri()
        logger.debug(f"Selected rhs base URI '{base_uri}' via file chooser.")
        self.rhs_base_uri_inventory_group.set_base_uri_from_file_chooser_button(file_chooser_button)

    def on_lhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        self.lhs_base_uri_inventory_group.apply_base_uri()

    def on_rhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        self.rhs_base_uri_inventory_group.apply_base_uri()

    def on_lhs_dataset_uri_set(self, file_chooser_button):
        self.lhs_base_uri_inventory_group.set_dataset_uri_from_file_chooser_button(file_chooser_button)

    def on_rhs_dataset_uri_set(self, file_chooser_button):
        self.rhs_base_uri_inventory_group.set_dataset_uri_from_file_chooser_button(file_chooser_button)

    def on_lhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.lhs_base_uri_inventory_group.apply_dataset_uri()

    def on_rhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.rhs_base_uri_inventory_group.apply_dataset_uri()

    def on_lhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is not None:
            self.lhs_base_uri_inventory_group.set_selected_dataset_row(list_box_row)

    def on_rhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and dataset when selected in right hand side list."""
        if list_box_row is not None:
            self.rhs_base_uri_inventory_group.set_selected_dataset_row(list_box_row)

    def on_lhs_dataset_list_auto_refresh_toggled(self, switch, state):
        logger.debug(f"LHS dataset list refresh toggled {'on' if state else 'off'}")
        self.lhs_base_uri_inventory_group.set_auto_refresh(state)
        self.lhs_base_uri_inventory_group.refresh()

    def on_rhs_dataset_list_auto_refresh_toggled(self, switch, state):
        logger.debug(f"RHS dataset list refresh toggled {'on' if state else 'off'}")
        self.rhs_base_uri_inventory_group.set_auto_refresh(state)
        self.rhs_base_uri_inventory_group.refresh()

    def on_main_switch_page(self, notebook, page, page_num):
        self.refresh(page_num)

    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    def on_jump_to_transfer_tab(self, button):
        self.main_notebook.set_current_page(TRANSFER_TAB)

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def on_window_destroy(self, *args):
        self.event_loop.stop()

    # generic methods

    def refresh(self, page_num=None):
        if page_num is None:
            page_num = self.main_notebook.get_current_page()
        if page_num == LOOKUP_TAB:
            self.lookup_tab.set_sensitive(True)
            self.direct_tab.set_sensitive(False)
            self.transfer_tab.set_sensitive(False)
            self.lookup_tab.refresh()
        elif page_num == DIRECT_TAB:
            self.lookup_tab.set_sensitive(False)
            self.direct_tab.set_sensitive(True)
            self.transfer_tab.set_sensitive(False)
            self.direct_tab.refresh()
        elif page_num == TRANSFER_TAB:
            self.lookup_tab.set_sensitive(False)
            self.direct_tab.set_sensitive(False)
            self.transfer_tab.set_sensitive(True)
            self.transfer_tab.refresh()


def run_gui():
    #base_path = os.path.abspath(os.path.dirname(__file__))
    #resource_path = os.path.join(base_path, '/de.uni-freiburg.dtool-lookup-gui.gresource')
    #resource = Gio.Resource.load(resource_path)
    #resource.register()

    # weird solution for registering custom widgets with gtk builder
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-lookup-gui.glade')

    loop = asyncio.get_event_loop()

    settings = Settings()

    signal_handler = SignalHandler(loop, builder, settings)

    # Connect to the lookup server upon startup
    signal_handler.lookup_tab.connect()

    loop.run_forever()
