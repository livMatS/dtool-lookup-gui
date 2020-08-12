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

from .LookupClient import LookupClient

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def fill_tree_store(store, data, parent=None):
    for i, current_data in enumerate(data):
        if len(data) != 1:
            current_parent = store.append(parent, [f'{i+1}', None])
        else:
            current_parent = parent
        for entry, value in current_data.items():
            if type(value) is list:
                current = store.append(current_parent, [entry, None])
                fill_tree_store(store, value, parent=current)
            else:
                print(entry, value)
                store.append(current_parent, [entry, str(value)])

class SignalHandler:
    def __init__(self, builder):
        self.builder = builder
        self.username = 'username'
        self.password = 'password'
        self.lookup = None

    def connect(self):
        self.lookup = LookupClient(self.username, self.password)
        self.datasets = self.lookup.all()
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

    def on_window_destroy(self, *args):
        Gtk.main_quit()

    def on_result_selected(self, list_box, list_box_row):
        print(list_box_row.dataset)
        dataset = list_box_row.dataset
        self.builder.get_object('dataset-name').set_text(dataset['name'])
        self.builder.get_object('dataset-uuid').set_text(dataset['uuid'])
        self.builder.get_object('dataset-uri').set_text(dataset['uri'])
        self.builder.get_object('dataset-created-by').set_text(dataset['creator_username'])
        self.builder.get_object('dataset-created-at').set_text(f'{datetime.fromtimestamp(dataset["created_at"])}')
        self.builder.get_object('dataset-frozen-at').set_text(f'{datetime.fromtimestamp(dataset["frozen_at"])}')

        readme = self.lookup.readme(dataset['uri'])
        readme_view = self.builder.get_object('dataset-readme')
        store = readme_view.get_model()
        store.clear()
        fill_tree_store(store, [readme])
        readme_view.show_all()

def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-gui.glade')

    signal_handler = SignalHandler(builder)
    signal_handler.connect()
    builder.connect_signals(signal_handler)

    win = builder.get_object('main-window')
    win.show_all()

    Gtk.main()
