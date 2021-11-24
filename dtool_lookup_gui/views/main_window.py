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


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/main_window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DtoolMainWindow'

    base_uri_button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()

    search_results_listbox = Gtk.Template.Child()

    uuid_label = Gtk.Template.Child()
    uri_label = Gtk.Template.Child()
    name_label = Gtk.Template.Child()
    created_by_label = Gtk.Template.Child()
    created_at_label = Gtk.Template.Child()
    frozen_at_label = Gtk.Template.Child()

    readme_treeview = Gtk.Template.Child()
    manufest_treeview = Gtk.Template.Child()


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
                if method_name in self.handlers:
                    logger.debug("Registering additional callback for '%s'" % (method_name))
                    self.handlers[method_name].append(method)
                else:
                    logger.debug("Registering callback for '%s'" % (method_name))
                    self.handlers[method_name] = Trampoline([method])

    # signal handlers

    def on_lhs_base_uri_set(self, file_chooser_button):
        """Base URI directory selected with file chooser."""
        base_uri = file_chooser_button.get_uri()
        logger.debug(f"Selected lhs base URI '{base_uri}' via file chooser.")
        self.lhs_base_uri_inventory_group.set_base_uri_from_file_chooser_button(file_chooser_button)

    def on_rhs_base_uri_set(self, file_chooser_button):
        """Base URI directory selected with file chooser."""
        base_uri = file_chooser_button.get_uri()
        logger.debug(f"Selected rhs base URI '{base_uri}' via file chooser.")
        self.rhs_base_uri_inventory_group.set_base_uri_from_file_chooser_button(file_chooser_button)

    def on_lhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        self.lhs_base_uri_inventory_group.apply_base_uri()

    def on_rhs_base_uri_open(self, button):
        """Open base URI button clicked."""
        self.rhs_base_uri_inventory_group.apply_base_uri()

    def on_lhs_dataset_uri_set(self, file_chooser_button):
        self.lhs_base_uri_inventory_group.set_dataset_uri_from_file_chooser_button(file_chooser_button)

    def on_rhs_dataset_uri_set(self, file_chooser_button):
        self.rhs_base_uri_inventory_group.set_dataset_uri_from_file_chooser_button(file_chooser_button)

    def on_lhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.lhs_base_uri_inventory_group.apply_dataset_uri()

    def on_rhs_dataset_uri_open(self, button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.rhs_base_uri_inventory_group.apply_dataset_uri()

    def on_lhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is not None:
            self.lhs_base_uri_inventory_group.set_selected_dataset_row(list_box_row)

    def on_rhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and dataset when selected in right hand side list."""
        if list_box_row is not None:
            self.rhs_base_uri_inventory_group.set_selected_dataset_row(list_box_row)

    def on_lhs_dataset_list_auto_refresh_toggled(self, switch, state):
        logger.debug(f"LHS dataset list refresh toggled {'on' if state else 'off'}")
        self.lhs_base_uri_inventory_group.set_auto_refresh(state)
        self.lhs_base_uri_inventory_group.refresh()

    def on_rhs_dataset_list_auto_refresh_toggled(self, switch, state):
        logger.debug(f"RHS dataset list refresh toggled {'on' if state else 'off'}")
        self.rhs_base_uri_inventory_group.set_auto_refresh(state)
        self.rhs_base_uri_inventory_group.refresh()

    def on_main_switch_page(self, notebook, page, page_num):
        self.refresh(page_num)

    def on_settings_clicked(self, widget):
        SettingsDialog(self).show()

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def on_window_destroy(self, *args):
        self.event_loop.stop()
