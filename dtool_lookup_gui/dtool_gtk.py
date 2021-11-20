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
# TODO: fill lists with one dataset when auto refresh toggled off
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GObject
import logging
import os
import urllib

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from . import date_to_string
from .models import DataSetModel, DataSetListModel, BaseURIModel, UnsupportedTypeError

logger = logging.getLogger(__name__)


DATASET_LIST_COLUMNS = ("uuid", "name", "size_str", "num_items", "creator", "date", "uri")
PROTO_DATASET_LIST_COLUMNS = ("uuid", "name", "creator", "uri")

HOME_DIR = os.path.expanduser("~")


# TODO: the progress bar does not work
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


class URISelector(ABC):
    """Groups text entry field, file chooser button, apply button."""
    def __init__(self, text_entry_buffer: Gtk.EntryBuffer):
        self._text_entry_buffer = text_entry_buffer
        self._text_entry = []
        self._button = []
        self._file_chooser_button = []

    # public
    def append_text_entry(self, text_entry: Gtk.Entry):
        self._text_entry.append(text_entry)

    def append_button(self, button: Gtk.Button):
        self._button.append(button)

    def append_file_chooser_button(self, file_chooser_button: Gtk.FileChooserButton):
        self._file_chooser_button.append(file_chooser_button)

    def apply_uri(self):
        """Usually when apply button clicked."""
        self._apply_uri()

    def set_uri_from_file_chooser_button(self, file_chooser_button: Gtk.FileChooserButton):
        """Set base URI directory selected with file chooser."""
        uri = file_chooser_button.get_uri()
        self._set_uri(uri)

    def set_sensitive(self, sensitive=True):
        """Enable or disable all elements."""
        for text_entry in self._text_entry:
            text_entry.set_sensitive(sensitive)
        for file_chooser_button in self._file_chooser_button:
            file_chooser_button.set_sensitive(sensitive)
        for button in self._button:
            button.set_sensitive(sensitive)

    def set_uri(self, uri):
        self._set_uri(uri)

    def _set_uri(self, uri):
        """Sets model base uri and associated file chooser and input field."""
        logger.debug(f"Set URI {uri}.")
        self._text_entry_buffer.set_text(uri, -1)

        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            for file_chooser_button in self._file_chooser_button:
                file_chooser_button.set_current_folder(fpath)

    @abstractmethod
    def _apply_uri(self):
        ...


class BaseURISelector(URISelector):
    """Groups text entry fields, file chooser buttons, apply buttons for base URI selection."""

    def __init__(self, base_uri_model: BaseURIModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base_uri_model = base_uri_model
        initial_base_uri = self._base_uri_model.get_base_uri()
        if initial_base_uri is None:
            initial_base_uri = HOME_DIR
        self.set_uri(initial_base_uri)

    def _apply_uri(self):
        uri = self._text_entry_buffer.get_text()
        self._base_uri_model.put_base_uri(uri)

    @property
    def base_uri_model(self):
        return self._base_uri_model


class DatasetURISelector(URISelector):
    """Groups text entry fields, file chooser buttons, apply buttons for dataset URI selection."""

    def __init__(self, dataset_model: DataSetModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dataset_model = dataset_model

    def _apply_uri(self):
        """Load dataset and deal with UnsupportedTypeError exceptions."""
        uri = self._text_entry_buffer.get_text()
        try:
            self._dataset_model.load_dataset(uri)
            # self.active_dataset_metadata_supported = True
        except UnsupportedTypeError:
            logger.warning("Dataset contains unsupported metadata type")
            # self.active_dataset_metadata_supported = False


    @property
    def dataset_model(self):
        return self._dataset_model


class DtoolDatasetListStore(Gtk.ListStore):
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


class DtoolDatasetListBox(Gtk.ListBox):
    # incredible lack of documentation for Gtk.Builder / PyGObject: needs __gtype_name__ to be registered properly below
    __gtype_name__ = 'DtoolDatasetListBox'


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



class BaseURIInventoryGroup:
    """Groups base uri selector, dataset selector with list store."""
    def __init__(self, base_uri_selector: BaseURISelector,
                 dataset_uri_selector: DatasetURISelector,
                 dataset_list_model: DataSetListModel):
        self._base_uri_selector = base_uri_selector
        self._dataset_uri_selector = dataset_uri_selector
        self._dataset_list_model = dataset_list_model
        self._error_callback = logger.warning
        self._dataset_list_box = []
        self._auto_refresh_switch = []
        self._auto_refresh = False
        self._selected_row = None

        # try to initialize list index
        try:
            self._dataset_list_model.set_active_index(0)
        except IndexError as exc:
            logger.debug(f"No entries in list model with base URI {self._dataset_list_model.base_uri}.")

        uri = self.get_selected_uri()
        if uri is not None:
            logger.debug(f"Initializing with dataset URI '{uri}'.")
            self.dataset_uri_selector.set_uri(uri)
            self.dataset_uri_selector.apply_uri()

    @property
    def base_uri_selector(self):
        return self._base_uri_selector

    @property
    def dataset_uri_selector(self):
        return self._dataset_uri_selector

    # TODO: cache selected URI also when refresh deactivated
    @property
    def auto_refresh(self):
        """If disabled, widget will not refresh content until enabled again."""
        return self._auto_refresh

    @auto_refresh.setter
    def auto_refresh(self, auto_refresh):
        self._auto_refresh = auto_refresh
        self._dataset_list_model.active_refresh = auto_refresh

    def set_auto_refresh(self, state):
        self.auto_refresh = state

    @property
    def dataset_model(self):
        return self._dataset_uri_selector.dataset_model

    @property
    def dataset_list_model(self):
        return self._dataset_list_model

    @property
    def selected_uri(self):
        return self.get_selected_uri()

    @property
    def base_uri(self):
        return self._base_uri_selector.base_uri_model.get_base_uri()

    def apply_base_uri(self):
        self._base_uri_selector.apply_uri()
        self.refresh()

    def apply_dataset_uri(self):
        self._dataset_uri_selector.apply_uri()

    def set_error_callback(self, error_callback):
        self._error_callback = error_callback

    def append_dataset_list_box(self, dataset_list_box: DtoolDatasetListBox):
        self._dataset_list_box.append(dataset_list_box)
        # self.refresh()

    def append_auto_refresh_switch(self, auto_refresh_switch: Gtk.Switch):
        self._auto_refresh_switch.append(auto_refresh_switch)
        # self.refresh()

    def get_selected_uri(self):
        return self._dataset_list_model.get_active_uri()

    def set_selected_dataset_uri(self, uri):
        self._dataset_uri_selector.set_uri(uri)
        self._dataset_uri_selector.apply_uri()
        self._dataset_list_model.set_active_index_by_uri(uri)

    def set_selected_dataset_row(self, row: DtoolDatasetListBoxRow):
        self.set_selected_dataset_uri(row.dataset['uri'])
        self._dataset_uri_selector.apply_uri()
        for dataset_list_box in self._dataset_list_box:
            dataset_list_box.select_row(row)

    def set_base_uri_from_file_chooser_button(self, file_chooser_button: Gtk.FileChooserButton):
        """Set base URI directory selected with file chooser."""
        uri = file_chooser_button.get_uri()
        self._base_uri_selector.set_uri_from_file_chooser_button(file_chooser_button)
        # self.refresh()

    def set_dataset_uri_from_file_chooser_button(self, file_chooser_button: Gtk.FileChooserButton):
        """Set base URI directory selected with file chooser."""
        uri = file_chooser_button.get_uri()
        self._dataset_uri_selector.set_uri_from_file_chooser_button(file_chooser_button)
        # self.refresh()

    def populate(self, selected_uri=None):
        # TODO: selection Gtk-native
        if selected_uri is None:
            selected_uri = self.get_selected_uri()

        try:
            self._dataset_list_model.reindex()
        except FileNotFoundError as exc:
            self._error_callback(exc.__str__())
            return

        # sort by name
        # TODO: sort field selection
        self._dataset_list_model.sort('name')

        for dataset_list_box in self._dataset_list_box:
            # TODO: targeted modifications instead of whole rebuild
            selected_row = None
            for props in self._dataset_list_model.yield_properties():
                row = DtoolDatasetListBoxRow()
                row.properties = props
                row.fill()
                if selected_row is None or selected_uri == row.dataset["uri"]:
                    # select the first row just in case the currently selected row is lost
                    selected_row = row
                dataset_list_box.add(row)

            if selected_row is not None:
                self.set_selected_dataset_uri(selected_row.dataset['uri'])
                dataset_list_box.select_row(selected_row)

            # self._dataset_uri_selector.apply_uri()
            dataset_list_box.show_all()

    def clear(self):
        for dataset_list_box in self._dataset_list_box:
            for entry in dataset_list_box:
                entry.destroy()

    def populate_one(self):
        if self.dataset_model.is_empty:
            return

        for dataset_list_box in self._dataset_list_box:
            row = DtoolDatasetListBoxRow()
            row.properties = self.dataset_model.dataset_info
            row.fill()
            dataset_list_box.add(row)

            if row is not None:
                self.set_selected_dataset_uri(row.dataset['uri'])
                dataset_list_box.select_row(row)

            dataset_list_box.show_all()

    def refresh(self, *args, **kwargs):
        for switch in self._auto_refresh_switch:
            switch.set_state(self._auto_refresh)

        self.clear()

        if not self._auto_refresh:
            logger.debug("No auto refresh, show only the currently selected dataset.")
            self.populate_one()
        else:
            # TODO: refine the refresh, pretty crude an inefficient now
            self.populate(*args, **kwargs)


GObject.type_register(DtoolDatasetListBox)
GObject.type_register(DtoolDatasetListBoxRow)
