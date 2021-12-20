#
# Copyright 2021 Johannes Hörmann
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
import datetime
import logging
import os

from gi.repository import Gdk, GLib, Gio, Gtk, GtkSource

from ..utils.logging import FormattedPrependingGtkTextBufferHandler

logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/log_window.ui')
class LogWindow(Gtk.Window):
    __gtype_name__ = 'DtoolLogWindow'

    log_text_view = Gtk.Template.Child()

    clear_button = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()

    log_switch = Gtk.Template.Child()
    # loglevel_entry = Gtk.Template.Child()
    loglevel_combo_box = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        root_logger = logging.getLogger()

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        # populate logleve selection combo box
        loglevel_store = Gtk.ListStore(int, str)
        configurable_loglevels = [
            (logging.CRITICAL, "CRITICAL"),
            (logging.ERROR, "ERROR"),
            (logging.WARNING, "WARNING"),
            (logging.INFO, "INFO"),
            (logging.DEBUG, "DEBUG"),
        ]

        self.loglevel_row_index_map = {}
        for row_index, (loglevel_value, loglevel_label) in enumerate(configurable_loglevels):
            loglevel_store.append([loglevel_value, loglevel_label])
            self.loglevel_row_index_map[loglevel_value] = row_index

        self.loglevel_combo_box.set_model(loglevel_store)
        self.loglevel_combo_box.set_active(self.loglevel_row_index_map[root_logger.level])
        self.loglevel_combo_box.connect("changed", self.on_loglevel_combo_box_changed)
        self.loglevel_combo_box.set_entry_text_column(1)

        # connect log handler to my buffer
        self.log_buffer = self.log_text_view.get_buffer()
        self.log_handler = FormattedPrependingGtkTextBufferHandler(
            text_buffer=self.log_buffer)

        # set up some pseudo highlighting for the log window
        lang_manager = GtkSource.LanguageManager()
        self.log_buffer.set_language(lang_manager.get_language("python"))
        self.log_buffer.set_highlight_syntax(True)
        self.log_buffer.set_highlight_matching_brackets(True)

        logger.debug("Append GtkTextBufferHandler to root logger.")
        root_logger.addHandler(self.log_handler)

        # bind another handler to th application-level action 'set-loglevel'
        set_loglevel_action = self.get_action_group("app").lookup_action('set-loglevel')
        set_loglevel_action.connect("change-state", self.do_loglevel_changed)

        root_logger.debug("Created log window.")

    # action handlers
    def do_loglevel_changed(self, action, value):
        """Keep entry ot loglevel combobox in sync with actual action state."""
        new_loglevel = value.get_uint16()
        logger.debug(f"Loglevel changed to {new_loglevel}, update combo box entry if necessary.")
        tree_iter = self.loglevel_combo_box.get_active_iter()
        model = self.loglevel_combo_box.get_model()
        current_loglevel, loglevel_label = model[tree_iter][:2]
        logger.debug(f"Current loglevel is {current_loglevel}.")
        if new_loglevel != current_loglevel:
            self.loglevel_combo_box.set_active(self.loglevel_row_index_map[new_loglevel])
            logger.debug(f"Combo box updated to row {self.loglevel_row_index_map[new_loglevel]}.")

    # signal handlers
    @Gtk.Template.Callback()
    def on_show(self, widget):
        logger.debug("Show.")
        root_logger = logging.getLogger()

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        logger.debug("Hide on delete.")
        return self.hide_on_delete()

    @Gtk.Template.Callback()
    def on_destroy(self, widget):
        logger.debug("Destroy.")
        root_logger = logging.getLogger()
        if self.log_handler in root_logger.handlers:
            root_logger.removeHandler(self.log_handler)

    @Gtk.Template.Callback()
    def on_log_switch_state_set(self, widget, state):
        logger.debug(f"{widget.get_name()} switched state to {state}")
        # Eventually managed to tie switch directly to action via glade
        # by setting up a stateful but parameterless toggle action
        # and specifying app.toggle-logging as action name for switch in xml,
        # hence no need for this handler anymore.

    @Gtk.Template.Callback()
    def on_loglevel_combo_box_changed(self, combo):
        """Selected loglevel from combo box."""
        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        loglevel, loglevel_label = model[tree_iter][:2]
        logger.debug(f"Selected ID: {loglevel}, loglevel: {loglevel_label}")
        # This explicitly evokes the according action when loglevel selected
        # in combo box turned, see
        # https://lazka.github.io/pgi-docs/Gio-2.0/classes/ActionGroup.html#Gio.ActionGroup.list_actions
        # There might be more elegant mechanism to connect a switch with an
        # app-central action, but the Gtk docs are sparse on actions...
        self.get_action_group("app").activate_action('set-loglevel', GLib.Variant.new_uint16(loglevel))

    @Gtk.Template.Callback()
    def on_clear_clicked(self, widget):
        """Clear contents of log window."""
        self.log_buffer.set_text("")

    @Gtk.Template.Callback()
    def on_copy_clicked(self, widget):
        """Copy contents of log window to clipboard."""
        start_iter = self.log_buffer.get_start_iter()
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.select_range(start_iter, end_iter)
        self.log_buffer.copy_clipboard(self.clipboard)
        logger.debug("Copied content of log window to clipboard.")

    @Gtk.Template.Callback()
    def on_save_clicked(self, widget):
        """Open file chooser dialog and save contents of log window to file."""
        dialog = Gtk.FileChooserDialog(title=f"Save log", parent=self,
                                       action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL,
                           Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK,
                           Gtk.ResponseType.OK)
        suggested_file_name = f"{datetime.datetime.now().isoformat()}-{self.get_application().get_application_id()}.log"
        dialog.set_current_name(suggested_file_name)
        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            start_iter = self.log_buffer.get_start_iter()
            end_iter = self.log_buffer.get_end_iter()
            dest_filename = dialog.get_filename()
            with open(dest_filename, "w") as file:
                file.write(self.log_buffer.get_text(start_iter, end_iter, include_hidden_chars=False))

        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()
