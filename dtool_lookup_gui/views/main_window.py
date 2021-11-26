#
# Copyright 2020 Lars Pastewka, Johanns Hoermann
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

import logging
import os

from gi.repository import Gtk

from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainMenu(Gtk.PopoverMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        vbox.add(Gtk.ModelButton(text='Settings'))
        vbox.add(Gtk.ModelButton(text='About dtool-lookup-gui'))
        self.add(vbox)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/main_window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DtoolMainWindow'

    menu_button = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()

    base_uri_list_box = Gtk.Template.Child()
    dataset_list_box = Gtk.Template.Child()

    uuid_label = Gtk.Template.Child()
    uri_label = Gtk.Template.Child()
    name_label = Gtk.Template.Child()
    created_by_label = Gtk.Template.Child()
    created_at_label = Gtk.Template.Child()
    frozen_at_label = Gtk.Template.Child()

    readme_treeview = Gtk.Template.Child()
    manifest_treeview = Gtk.Template.Child()

    settings_button = Gtk.Template.Child()

    @Gtk.Template.Callback()
    def on_show_window(self, widget):
        self.base_uri_list_box.refresh()

    @Gtk.Template.Callback()
    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    @Gtk.Template.Callback()
    def on_base_uri_selected(self, list_box, row):
        self.dataset_list_box.refresh(row.base_uri)

    @Gtk.Template.Callback()
    def on_dataset_selected(self, list_box, row):
        self._update_dataset_view(row.dataset)

    def _update_dataset_view(self, dataset):
        self.uuid_label.set_text(dataset.uuid)
        self.uri_label.set_text(dataset.uri)
        self.name_label.set_text(dataset.name)
        self.created_by_label.set_text(dataset.creator)
        #self.created_at_label.set_text(dataset.created_at)
        self.frozen_at_label.set_text(dataset.date)
