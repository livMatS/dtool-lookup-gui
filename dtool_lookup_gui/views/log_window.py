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

from gi.repository import Gio, Gtk, GtkSource

from ..utils.logging import FormattedGtkTextBufferHandler

logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/log_window.ui')
class LogWindow(Gtk.Window):
    __gtype_name__ = 'DtoolLogWindow'

    log_text_view = Gtk.Template.Child()

    clear_button = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()

    log_switch = Gtk.Template.Child()
    loglevel_entry = Gtk.Template.Child()
    loglevel_combo_box = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log_buffer = self.log_text_view.get_buffer()
        self.log_handler = FormattedGtkTextBufferHandler(text_buffer=self.log_buffer)

        lang_manager = GtkSource.LanguageManager()
        self.log_buffer.set_language(lang_manager.get_language("python"))
        self.log_buffer.set_highlight_syntax(True)
        self.log_buffer.set_highlight_matching_brackets(True)

        root_logger = logging.getLogger()
        if self.log_handler not in root_logger.handlers:
            logger.debug("Append GtkTextBufferHandler to root logger.")
            root_logger.addHandler(self.log_handler)

        root_logger.debug("Added handler.")

    # signal handlers
    @Gtk.Template.Callback()
    def on_show(self, widget):
        root_logger = logging.getLogger()
        if self.log_handler not in root_logger.handlers:
            root_logger.addHandler(self.log_handler)

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        return self.hide_on_delete()

    @Gtk.Template.Callback()
    def on_destroy(self, widget):
        root_logger = logging.getLogger()
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