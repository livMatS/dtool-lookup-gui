import dtoolcore
import gi
gi.require_version('Gtk', '3.0')
# gi.require_version('dtool_gtk', '0.1')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, Gio, GtkSource, GObject
import logging

from . import date_to_string

logger = logging.getLogger(__name__)


DATASET_LIST_COLUMNS = ("uuid", "name", "size_str", "num_items", "creator", "date", "uri")
PROTO_DATASET_LIST_COLUMNS = ("uuid", "name", "creator", "uri")


class DtoolDatasetListBox(Gtk.ListBox):
    # incredible lack of documentation for Gtk.Builder / PyGObject: needs __gtype_name__ to be registered properly below
    __gtype_name__ = 'DtoolDatasetListBox'

    def __init__(self, *args, **kwargs):
        self._dataset_list_model = None
        self._base_uri_model = None
        self._error_callback = logger.warning
        super().__init__(*args, **kwargs)

    @property
    def base_uri_model(self):
        return self._base_uri_model

    @base_uri_model.setter
    def base_uri_model(self, base_uri_model):
        self._base_uri_model = base_uri_model
        self._dataset_list_model.set_base_uri_model(self._base_uri_model)

    @property
    def base_uri(self):
        return self._base_uri_model.get_base_uri()

    @base_uri.setter
    def base_uri(self, base_uri):
        logger.debug(f"Put base URI {base_uri}.")
        self._base_uri_model.put_base_uri(base_uri)

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
        self.selected_uri = selected_row.dataset['uri']
        self.show_all()

    def refresh(self, *args, **kwargs):
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