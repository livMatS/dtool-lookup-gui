#
# Copyright 2021 Johanns Hoermann, Lars Pastewka
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

from gi.repository import GLib, Gio, Gtk, GtkSource

from ..utils.logging import GtkTextBufferHandler

_logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/log_window.ui')
class LogWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DtoolLogWindow'

    log_text_view = Gtk.Template.Child()

    clear_button = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    save_file_chooser_button = Gtk.Template.Child()

    enable_logging_switch = Gtk.Template.Child()
    loglevel_combo_box = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        root_logger = logging.getLogger()

        # toggle-logging
        toggle_logging_variant = GLib.Variant.new_bool(False)
        toggle_logging_action = Gio.SimpleAction.new_stateful(
            "toggle_logging", toggle_logging_variant.get_type(), toggle_logging_variant
        )
        toggle_logging_action.connect("change-state", self.on_toggle_logging)
        self.add_action(toggle_logging_action)

        # change-loglevel
        loglevel_variant = GLib.Variant.new_uint16(root_logger.level)
        loglevel_action = Gio.SimpleAction.new_stateful(
            "change_loglevel", loglevel_variant.get_type(), loglevel_variant
        )
        loglevel_action.connect("change-state", self.on_change_loglevel)
        self.add_action(loglevel_action)

        self.log_buffer = self.log_text_view.get_buffer()

        self.log_handler = GtkTextBufferHandler(self.log_buffer)

        # logger = logging.getLogger()
        # root_logger.addHandler(self.log_handler)

        lang_manager = GtkSource.LanguageManager()
        self.log_buffer.set_language(lang_manager.get_language("python"))
        self.log_buffer.set_highlight_syntax(True)
        self.log_buffer.set_highlight_matching_brackets(True)

    def toggle_logging(self, action, value):
        action.set_state(value)
        root_logger = logging.getLogger()
        if value.get_boolean():
            if not self.log_handler in root_logger.handlers:
                root_logger.addHandler(self.log_handler)
        else:
            if self.log_handler in root_logger.handlers:
                root_logger.removeHandler(self.log_handler)

    @Gtk.Template.Callback()
    def on_log_switch_activate(self, widget):
        pass

    @Gtk.Template.Callback()
    def on_loglevel_combo_box_changed(self, widget):
        pass

    @Gtk.Template.Callback()
    def on_clear_clicked(self, widget):
        self.log_buffer.set_text("")

    @Gtk.Template.Callback()
    def on_copy_clicked(self, widget):
        pass

    @Gtk.Template.Callback()
    def on_save_clicked(self, widget):
        pass
