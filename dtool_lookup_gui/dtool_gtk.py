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
# TODO: remove selected_uri property
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GObject
import logging

from contextlib import AbstractContextManager
from . import date_to_string

logger = logging.getLogger(__name__)


DATASET_LIST_COLUMNS = ("uuid", "name", "size_str", "num_items", "creator", "date", "uri")
PROTO_DATASET_LIST_COLUMNS = ("uuid", "name", "creator", "uri")


class ProgressBar(AbstractContextManager):
    """Mimics click.progressbar"""
    def __init__(self, length=None, label=None, pb=None):
        if pb is None:
            pb = Gtk.ProgressBar(show_text=True, text=None)
        self._pb = pb
        self._item_show_func = None
        self._label_template = '{label:}'
        self._label_item_template = '{label:} ({item:})'
        self._label = label
        self._length = length
        self._step = 0

    def __enter__(self):
        self._pb.set_fraction(0.0)
        self._set_text()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label):
        self._label = label
        self._set_text()

    @property
    def item_show_func(self):
        return self._item_show_func

    @item_show_func.setter
    def item_show_func(self, item_show_func):
        self._item_show_func = item_show_func
        self._set_text()

    def update(self, step):
        self._step += step
        self._pb.set_fraction(float(self._step) / float(self._length))
        self._set_text()

    def _set_text(self):
        if self._label is not None and self._item_show_func is not None:
            self._pb.set_text(self._label_item_template.format(
                label=self._label, item=self.item_show_func(self._step)))
        if self._label is not None:
            self._pb.set_text(self._label_template.format(label=self._label))
        else:
            self._pb.set_show_text(False)


class DtoolDatasetListBox(Gtk.ListBox):
    # incredible lack of documentation for Gtk.Builder / PyGObject: needs __gtype_name__ to be registered properly below
    __gtype_name__ = 'DtoolDatasetListBox'

    def __init__(self, *args, **kwargs):
        self._auto_refresh = False
        self._dataset_list_model = None
        # self._base_uri_model = None
        self._error_callback = logger.warning
        super().__init__(*args, **kwargs)

    @property
    def base_uri_model(self):
        # return self._base_uri_model
        return self._dataset_list_model._base_uri_model

    @base_uri_model.setter
    def base_uri_model(self, base_uri_model):
        # self._base_uri_model = base_uri_model
        logger.debug(f"Set base URI model with URI {base_uri_model.get_base_uri()},")
        self._dataset_list_model.set_base_uri_model(base_uri_model)

    @property
    def base_uri(self):
        # return self._dataset_list_model.base_uri_model.get_base_uri()
        return self._dataset_list_model.base_uri

    # @base_uri.setter
    # def base_uri(self, base_uri):
    #    logger.debug(f"Put base URI {base_uri}.")
    #    self._base_uri_model.put_base_uri(base_uri)

    @property
    def dataset_list_model(self):
        return self._dataset_list_model

    @dataset_list_model.setter
    def dataset_list_model(self, dataset_list_model):
        self._dataset_list_model = dataset_list_model

    @property
    def selected_uri(self):
        return self._dataset_list_model.get_active_uri()

    @selected_uri.setter
    def selected_uri(self, uri):
        self._dataset_list_model.set_active_index_by_uri(uri)

    # TODO: cache selected URI also when refresh deactivated
    @property
    def auto_refresh(self):
        """If disabled, widget will not refresh content until enabled again."""
        return self._auto_refresh

    @auto_refresh.setter
    def auto_refresh(self, auto_refresh):
        self._auto_refresh = auto_refresh
        self._dataset_list_model.active_refresh = auto_refresh

    def set_error_callback(self, error_callback):
        self._error_callback = error_callback

    def populate(self, selected_uri=None):
        # TODO: selection Gtk-native
        if selected_uri is None:
            selected_uri = self.selected_uri

        try:
            self._dataset_list_model.reindex()
        except FileNotFoundError as exc:
            self._error_callback(exc.__str__())
            return

        # sort by name
        # TODO: sort field selection
        self._dataset_list_model.sort('name')

        for entry in self:
            entry.destroy()

        selected_row = None
        for props in self._dataset_list_model.yield_properties():
            row = DtoolDatasetListBoxRow()
            row.properties = props
            row.fill()
            if selected_row is None or selected_uri == row.dataset["uri"]:
                # select the first row just in case the currently selected row is lost
                selected_row = row

            self.add(row)

        self.select_row(selected_row)
        if selected_row is not None:
            self.selected_uri = selected_row.dataset['uri']
        self.show_all()

    def refresh(self, *args, **kwargs):
        if not self._auto_refresh:
            logger.debug("No auto refresh, skip.")
            return

        # TODO: refine
        self.populate(*args, **kwargs)


class DtoolDatasetListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolDatasetListBoxRow'

    def __init__(self, *args, **kwargs):
        self._dataset = None
        self._props = None
        super().__init__(*args, **kwargs)

    @property
    def properties(self):
        return self._props

    @properties.setter
    def properties(self, props):
        self._props = props

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    def fill(self):
        # TODO: other way for distinguishing frozen and proto
        is_frozen = "date" in self._props

        if is_frozen:
            values = [self._props[c] for c in DATASET_LIST_COLUMNS]
            d = {c: v for c, v in zip(DATASET_LIST_COLUMNS, values)}
            prefix = ''
        else:
            values = [self._props[c] for c in PROTO_DATASET_LIST_COLUMNS]
            d = {c: v for c, v in zip(PROTO_DATASET_LIST_COLUMNS, values)}
            prefix = '*'

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

        self.add(vbox)
        self.dataset = d


GObject.type_register(DtoolDatasetListBox)
GObject.type_register(DtoolDatasetListBoxRow)