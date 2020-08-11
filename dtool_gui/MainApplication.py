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
from datetime import datetime

import gi

from .LookupClient import LookupClient

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SignalHandler:
    def __init__(self, builder):
        self.builder = builder
        self.username = 'user'
        self.password = 'password'
        self.lookup = None

    def connect(self):
        self.lookup = LookupClient(self.username, self.password)
        self.datasets = self.lookup.all()
        results_widget = self.builder.get_object('search-results')
        for dataset in self.datasets:
            row = Gtk.ListBoxRow()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{dataset["name"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{dataset["uuid"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(
                f'<small>Created by: {dataset["creator_username"]}, '
                f'frozen at: '
                f'{datetime.fromtimestamp(dataset["frozen_at"])}</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = dataset
            row.add(vbox)
            results_widget.add(row)
        results_widget.show_all()

    def on_window_destroy(self, *args):
        print('onDestroy')
        Gtk.main_quit()

    def on_result_selected(self, list_box, list_box_row):
        print(list_box_row.dataset)
        dataset = list_box_row.dataset
        self.builder.get_object('dataset-name').set_text(dataset['name'])
        self.builder.get_object('dataset-uuid').set_text(dataset['uuid'])
        self.builder.get_object('dataset-uri').set_text(dataset['uri'])


def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-gui.glade')

    signal_handler = SignalHandler(builder)
    signal_handler.connect()
    builder.connect_signals(signal_handler)

    win = builder.get_object('main-window')
    win.show_all()

    Gtk.main()
