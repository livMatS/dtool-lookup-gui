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
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

from . import date_to_string

from .models import (
    LocalBaseURIModel,
    DataSetListModel,
    DataSetModel,
    ProtoDataSetModel,
    MetadataSchemaListModel,
    UnsupportedTypeError,
    BaseURIModel,
)


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        # local dataset management
        self.base_uri_model = BaseURIModel()
        self.dataset_list_model = DataSetListModel()
        self.dataset_model = DataSetModel()

        # Configure the models.
        self.dataset_list_model.set_base_uri_model(self.base_uri_model)

    def on_base_uri_set(self,  filechooserbutton):
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        base_uri_entry_buffer.set_text(filechooserbutton.get_uri(), -1)

    def on_base_uri_open(self,  button):
        base_uri_entry_buffer = self.builder.get_object('base-uri-entry-buffer')
        results_widget = self.builder.get_object('dtool-ls-results')
        statusbar_widget = self.builder.get_object('main-statusbar')

        # base_uri = filechooserbutton.get_filename()
        base_uri = base_uri_entry_buffer.get_text()
        self.base_uri_model.put_base_uri(base_uri)

        self.dataset_list_model.reindex()
        statusbar_widget.push(0, f'{len(self.dataset_list_model._datasets)} datasets.')

        for entry in results_widget:
            entry.destroy()

        first_row = None

        dataset_list_columns = ("uuid", "name", "size_str", "num_items", "creator", "date")
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

