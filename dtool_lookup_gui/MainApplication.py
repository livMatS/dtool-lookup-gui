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
#import asyncio_glib
#asyncio.set_event_loop_policy(asyncio_glib.GLibEventLoopPolicy())

from . import LookupTab, DirectTab
from dtool_lookup_gui.dtool_gtk import DtoolDatasetListBox, DtoolDatasetListBoxRow
logger = logging.getLogger(__name__)

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

        self.main_window = self.builder.get_object('main-window')
        self.settings_window = self.builder.get_object('settings-window')

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        self.error_bar.set_revealed(False)

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.lookup_tab = LookupTab.SignalHandler(event_loop, builder, settings)
        self.direct_tab = DirectTab.SignalHandler(event_loop, builder, settings)

        # Create a dictionary to hold the signal-handler pairs
        self.handlers = {}

        # load all signal handlers into sel.handlers
        self._load_handlers(self.lookup_tab)
        self._load_handlers(self.direct_tab)
        self._load_handlers(self)

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

    def on_main_switch_page(self, notebook, page, page_num):
        if page_num == LOOKUP_TAB:
            self.lookup_tab.set_sensitive(True)
            self.direct_tab.set_sensitive(False)
            self.lookup_tab.refresh()
        elif page_num == DIRECT_TAB:
            self.lookup_tab.set_sensitive(False)
            self.direct_tab.set_sensitive(True)
            self.direct_tab.refresh()
        elif page_num == TRANSFER_TAB:
            self.show_error("Not implemented.")

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
