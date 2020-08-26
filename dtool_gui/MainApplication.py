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

import os
from datetime import date, datetime

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

import asyncio, gbulb

gbulb.install(gtk=True)

from .LookupClient import LookupClient


def fill_tree_store(store, data, parent=None):
    for i, current_data in enumerate(data):
        if len(data) != 1:
            current_parent = store.append(parent, [f'{i + 1}', None])
        else:
            current_parent = parent
        for entry, value in current_data.items():
            if type(value) is list:
                current = store.append(current_parent, [entry, None])
                fill_tree_store(store, value, parent=current)
            else:
                store.append(current_parent, [entry, str(value)])


class Settings:
    def __init__(self):
        self.settings = Gio.Settings.new('de.uni-freiburg.dtool-gui')

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

        self._search_task = None

    def _refresh_results(self):
        results_widget = self.builder.get_object('search-results')
        for dataset in sorted(self.datasets, key=lambda d: -d['frozen_at']):
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
                f'{date.fromtimestamp(dataset["frozen_at"])}</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = dataset
            row.add(vbox)
            results_widget.add(row)
        results_widget.show_all()

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
        print(list_box_row.dataset)
        dataset = list_box_row.dataset
        self.builder.get_object('dataset-name').set_text(dataset['name'])
        self.builder.get_object('dataset-uuid').set_text(dataset['uuid'])
        self.builder.get_object('dataset-uri').set_text(dataset['uri'])
        self.builder.get_object('dataset-created-by').set_text(
            dataset['creator_username'])
        self.builder.get_object('dataset-created-at').set_text(
            f'{datetime.fromtimestamp(dataset["created_at"])}')
        self.builder.get_object('dataset-frozen-at').set_text(
            f'{datetime.fromtimestamp(dataset["frozen_at"])}')

        async def fetch_readme():
            readme_view = self.builder.get_object('dataset-readme')
            store = readme_view.get_model()
            store.clear()
            readme = await self.lookup.readme(dataset['uri'])
            fill_tree_store(store, [readme])
            readme_view.show_all()

        self._readme_task = asyncio.create_task(fetch_readme())

    def on_search(self, search_entry):
        async def fetch_search_result():
            keyword = search_entry.get_text()
            self.dataset = await self.lookup.search(keyword)
            print(keyword, len(self.datasets))

        if self._search_task is not None:
            self._search_task.cancel()
        self._search_task = asyncio.create_task(fetch_search_result())


def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-gui.glade')

    loop = asyncio.get_event_loop()

    signal_handler = SignalHandler(loop, builder, Settings())
    builder.connect_signals(signal_handler)

    win = builder.get_object('main-window')
    win.show_all()

    # Connect to the lookup server upon startup
    loop.create_task(signal_handler.connect())

    loop.run_forever()
