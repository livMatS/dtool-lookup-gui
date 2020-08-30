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
import locale
import math
import os
from contextlib import contextmanager
from datetime import date, datetime

import dtoolcore

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

import gbulb

gbulb.install(gtk=True)

from .LookupClient import LookupClient


@contextmanager
def time_locale(name):
    # This code snippet was taken from:
    # https://stackoverflow.com/questions/18593661/how-do-i-strftime-a-date-object-in-a-different-locale
    saved = locale.setlocale(locale.LC_TIME)
    try:
        yield locale.setlocale(locale.LC_TIME, name)
    finally:
        locale.setlocale(locale.LC_TIME, saved)


def to_timestamp(d):
    """
    Convert a sting or a timestamp to a timestamp. This is a dirty fix necessary
    because the /dataset/list route return timestamps but /dataset/search
    returns strings.
    """
    if type(d) is str:
        try:
            with time_locale('C'):
                d = dtoolcore.utils.timestamp(
                    datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z'))
        except ValueError as e:
            d = -1
    return d


def datetime_to_string(d):
    return datetime.fromtimestamp(to_timestamp(d))


def date_to_string(d):
    return date.fromtimestamp(to_timestamp(d))


def human_readable_file_size(num, suffix='B'):
    # From: https://gist.github.com/cbwar/d2dfbc19b140bd599daccbe0fe925597
    if num == 0:
        return '0B'
    magnitude = int(math.floor(math.log(num, 1024)))
    val = num / math.pow(1024, magnitude)
    if magnitude > 7:
        return '{:.1f}{}{}'.format(val, 'Yi', suffix)
    return '{:3.1f}{}{}'.format(val,
                                ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'][
                                    magnitude], suffix)


def fill_readme_tree_store(store, data, parent=None):
    for i, current_data in enumerate(data):
        if len(data) != 1:
            current_parent = store.append(parent, [f'{i + 1}', None])
        else:
            current_parent = parent
        for entry, value in current_data.items():
            if type(value) is list:
                current = store.append(current_parent, [entry, None])
                fill_readme_tree_store(store, value, parent=current)
            else:
                store.append(current_parent, [entry, str(value)])


def fill_manifest_tree_store(store, data, parent=None):
    for uuid, values in data.items():
        store.append(parent,
                     [values['relpath'],
                      human_readable_file_size(values['size_in_bytes']),
                      f'{date_to_string(values["utc_timestamp"])}',
                      uuid])


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.dirname(__file__), Gio.SettingsSchemaSource.get_default(),
            False)
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-gui", False)
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


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        self.event_loop = event_loop
        self.builder = builder
        self.settings = settings
        self.lookup = None

        self.main_window = self.builder.get_object('main-window')
        self.settings_window = self.builder.get_object('settings-window')

        self._search_task = None

        self._selected_dataset = None
        self._readme = None
        self._manifest = None

    def _refresh_results(self):
        results_widget = self.builder.get_object('search-results')
        statusbar_widget = self.builder.get_object('main-statusbar')
        statusbar_widget.push(0, f'{len(self.datasets)} datasets')
        for entry in results_widget:
            entry.destroy()
        for dataset in sorted(self.datasets,
                              key=lambda d: -to_timestamp(d['frozen_at'])):
            row = Gtk.ListBoxRow()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{dataset["uuid"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{dataset["name"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(
                f'<small>Created by: {dataset["creator_username"]}, '
                f'frozen at: '
                f'{date_to_string(dataset["frozen_at"])}</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = dataset
            row.add(vbox)
            results_widget.add(row)
        results_widget.show_all()

    async def _fetch_readme(self, uri):
        readme_view = self.builder.get_object('dataset-readme')
        store = readme_view.get_model()
        store.clear()
        self._readme = await self.lookup.readme(uri)
        fill_readme_tree_store(store, [self._readme])
        readme_view.columns_autosize()
        readme_view.show_all()

    async def _fetch_manifest(self, uri):
        manifest_view = self.builder.get_object('dataset-manifest')
        store = manifest_view.get_model()
        store.clear()
        self._manifest = await self.lookup.manifest(uri)
        print(self._manifest)
        fill_manifest_tree_store(store, self._manifest['items'])
        manifest_view.columns_autosize()
        manifest_view.show_all()

    async def connect(self):
        self.lookup = LookupClient(self.settings.lookup_url,
                                   self.settings.authenticator_url,
                                   self.settings.username,
                                   self.settings.password)
        await self.lookup.connect()
        self.datasets = await self.lookup.all()
        self._refresh_results()

    def on_window_destroy(self, *args):
        self.event_loop.stop()

    def on_result_selected(self, list_box, list_box_row):
        self._selected_dataset = list_box_row.dataset
        self._readme = None
        self._manifest = None

        self.builder.get_object('dataset-name').set_text(
            self._selected_dataset['name'])
        self.builder.get_object('dataset-uuid').set_text(
            self._selected_dataset['uuid'])
        self.builder.get_object('dataset-uri').set_text(
            self._selected_dataset['uri'])
        self.builder.get_object('dataset-created-by').set_text(
            self._selected_dataset['creator_username'])
        self.builder.get_object('dataset-created-at').set_text(
            f'{datetime_to_string(self._selected_dataset["created_at"])}')
        self.builder.get_object('dataset-frozen-at').set_text(
            f'{datetime_to_string(self._selected_dataset["frozen_at"])}')

        page = self.builder.get_object('dataset-notebook').get_property('page')
        if page == 0:
            self._readme_task = asyncio.create_task(
                self._fetch_readme(self._selected_dataset['uri']))
        elif page == 1:
            self._manifest_task = asyncio.create_task(
                self._fetch_manifest(self._selected_dataset['uri']))

    def on_search(self, search_entry):
        async def fetch_search_result():
            keyword = search_entry.get_text()
            if keyword:
                self.datasets = await self.lookup.search(keyword)
            else:
                self.datasets = await self.lookup.all()
            self._refresh_results()

        if self._search_task is not None:
            self._search_task.cancel()
        self._search_task = asyncio.create_task(fetch_search_result())

    def on_settings_clicked(self, user_data):
        self.settings_window.show()

    def on_delete_settings(self, event, user_data):
        self.settings_window.hide()
        # Reconnect since settings may have been changed
        asyncio.create_task(self.connect())
        return True

    def on_switch_page(self, notebook, page, page_num):
        if self._selected_dataset is not None:
            print(page_num)
            if page_num == 0 and self._readme is None:
                self._readme_task = asyncio.create_task(
                    self._fetch_readme(self._selected_dataset['uri']))
            if page_num == 1 and self._manifest is None:
                self._manifest_task = asyncio.create_task(
                    self._fetch_manifest(self._selected_dataset['uri']))


def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-gui.glade')

    loop = asyncio.get_event_loop()

    settings = Settings()

    signal_handler = SignalHandler(loop, builder, settings)
    builder.connect_signals(signal_handler)

    builder.get_object('main-window').show_all()

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

    # Connect to the lookup server upon startup
    loop.create_task(signal_handler.connect())

    loop.run_forever()
