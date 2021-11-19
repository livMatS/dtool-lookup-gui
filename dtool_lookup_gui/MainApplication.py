#
# Copyright 2020 Lars Pastewka
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

import dtool_lookup_api.core.config
dtool_lookup_api.core.config.Config.interactive = False

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, Gio, GtkSource, GObject

import gbulb
gbulb.install(gtk=True)

from . import GlobalConfig, LookupTab, DirectTab, TransferTab
from .models import (
    LocalBaseURIModel,
    RemoteBaseURIModel,
    DataSetListModel,
    DataSetModel,
    UnsupportedTypeError,
)

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
        for m in self.methods:
            m(*args, **kwargs)

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

    @property
    def lookup_url(self):
        return self.settings.get_string('lookup-url')

    @property
    def authenticator_url(self):
        return self.settings.get_string('authenticator-url')

    @property
    def username(self):
        return self.settings.get_string('lookup-username')

    @property
    def password(self):
        return self.settings.get_string('lookup-password')

    @property
    def dependency_keys(self):
        return self.settings.get_string('dependency-keys')


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        self.event_loop = event_loop
        self.builder = builder
        self.settings = settings

        # gui elements
        self.lhs_base_uri_entry_buffer = self.builder.get_object('lhs-base-uri-entry-buffer')
        self.lhs_dataset_uri_entry_buffer = self.builder.get_object('lhs-dataset-uri-entry-buffer')
        self.rhs_base_uri_entry_buffer = self.builder.get_object('rhs-base-uri-entry-buffer')
        self.rhs_dataset_uri_entry_buffer = self.builder.get_object('rhs-dataset-uri-entry-buffer')

        self.main_window = self.builder.get_object('main-window')
        self.settings_window = self.builder.get_object('settings-window')

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        # models
        self.lhs_dataset_list_model = DataSetListModel()
        self.lhs_base_uri_model = LocalBaseURIModel()
        self.lhs_dataset_model = DataSetModel()
        self.lhs_dataset_list_model.set_base_uri_model(self.lhs_base_uri_model)

        self.rhs_dataset_list_model = DataSetListModel()
        self.rhs_base_uri_model = RemoteBaseURIModel()
        # self.rhs_dataset_model = DataSetModel()
        self.rhs_dataset_list_model.set_base_uri_model(self.rhs_base_uri_model)

        #configure
        self.lhs_dataset_list_model.auto_refresh = GlobalConfig.auto_refresh_on
        self.rhs_dataset_list_model.auto_refresh = GlobalConfig.auto_refresh_on

        initial_base_uri = self.lhs_base_uri_model.get_base_uri()
        if initial_base_uri is None:
            initial_base_uri = HOME_DIR
        self._set_lhs_base_uri(initial_base_uri)

        self.error_bar.set_revealed(False)

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.lookup_tab = LookupTab.SignalHandler(self)
        self.direct_tab = DirectTab.SignalHandler(self)
        self.transfer_tab = TransferTab.SignalHandler(self)

        # Create a dictionary to hold the signal-handler pairs
        self.handlers = {}

        # load all signal handlers into sel.handlers
        self._load_handlers(self)
        self._load_handlers(self.lookup_tab)
        self._load_handlers(self.direct_tab)
        self._load_handlers(self.transfer_tab)

        self.builder.connect_signals(self.handlers)
        self.builder.get_object('main-window').show_all()

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
                logger.debug("Registering callback %s" % (method_name))
                if method_name in self.handlers:
                    self.handlers[method_name].append(method)
                else:
                    self.handlers[method_name] = Trampoline([method])

    def on_lhs_base_uri_set(self, filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
        logger.debug(f"Selected lhs base URI '{base_uri}' via file chooser.")
        self._set_lhs_base_uri(base_uri)

    def on_rhs_base_uri_set(self, filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
        logger.debug(f"Selected rhs base URI '{base_uri}' via file chooser.")
        self._set_rhs_base_uri(base_uri)

    def on_lhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        base_uri = self.lhs_base_uri_entry_buffer.get_text()
        logger.debug(f"lhs base URI open button clicked for {base_uri}.")
        self.lhs_base_uri_model.put_base_uri(base_uri)

    def on_rhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        base_uri = self.rhs_base_uri_entry_buffer.get_text()
        logger.debug(f"rhs base URI open button clicked for {base_uri}.")
        self.rhs_base_uri_model.put_base_uri(base_uri)

    def on_lhs_dataset_uri_set(self, filechooserbutton):
        self._set_lhs_dataset_uri(filechooserbutton.get_uri())

    def on_rhs_dataset_uri_set(self, filechooserbutton):
        self._set_rhs_dataset_uri(filechooserbutton.get_uri())

    def on_lhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        uri = self.lhs_dataset_uri_entry_buffer.get_text()
        self.lhs_dataset_list_model.set_active_index_by_uri(uri)

    def on_rhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        uri = self.rhs_dataset_uri_entry_buffer.get_text()
        self.rhs_dataset_list_model.set_active_index_by_uri(uri)

    def on_main_switch_page(self, notebook, page, page_num):
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

    def on_settings_clicked(self, user_data):
        asyncio.create_task(self._fetch_users())
        self.settings_window.show()

    def on_delete_settings(self, event, user_data):
        self.settings_window.hide()
        # Reconnect since settings may have been changed
        asyncio.create_task(self.lookup_tab.connect())
        return True

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def on_window_destroy(self, *args):
        self.event_loop.stop()

    # private methods
    def _set_lhs_base_uri(self, uri):
        """Sets lhs base uri and associated file chooser and input field."""
        logger.debug(f"Set lhs base URI {uri}.")
        self.lhs_base_uri_model.put_base_uri(uri)
        self.lhs_base_uri_entry_buffer.set_text(self.lhs_base_uri_model.get_base_uri(), -1)

    def _set_rhs_base_uri(self, uri):
        """Set dataset file chooser and input field."""
        logger.debug(f"Set rhs base URI {uri}.")
        self.rhs_base_uri_model.put_base_uri(uri)
        self.rhs_base_uri_entry_buffer.set_text(self.rhs_base_uri_model.get_base_uri(), -1)

    def _set_lhs_dataset_uri(self, uri):
        """Set dataset file chooser and input field."""
        logger.debug(f"Set lhs dataset URI {uri}.")
        self.lhs_dataset_uri_entry_buffer.set_text(uri, -1)
        self.lhs_dataset_list_model.set_active_index_by_uri(uri)

    def _set_rhs_dataset_uri(self, uri):
        """Set dataset file chooser and input field."""
        logger.debug(f"Set rhs dataset URI {uri}.")
        self.rhs_dataset_uri_entry_buffer.set_text(uri, -1)
        self.rhs_dataset_list_model.set_active_index_by_uri(uri)


def run_gui():
    # weird solution for registering custom widgets with gtk builder
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-lookup-gui.glade')

    loop = asyncio.get_event_loop()

    settings = Settings()

    signal_handler = SignalHandler(loop, builder, settings)
    # builder.connect_signals(signal_handler)

    settings.settings.bind("lookup-url", builder.get_object('lookup-url-entry'),
                           'text', Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("authenticator-url",
                           builder.get_object('authenticator-url-entry'),
                           'text', Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("lookup-username",
                           builder.get_object('username-entry'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("lookup-password",
                           builder.get_object('password-entry'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("dependency-keys",
                           builder.get_object('dependency-keys'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)

    # Connect to the lookup server upon startup
    signal_handler.lookup_tab.connect()

    loop.run_forever()
