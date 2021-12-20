#
# Copyright 2021 Lars Pastewka
#           2021 Johannes Hörmann
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
import logging
import os

from gi.repository import GLib, Gdk, Gtk, GtkSource

from ..utils.query import (
    single_line_sanitize_query_text,
    multi_line_sanitize_query_text)

logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/search_popover.ui')
class DtoolSearchPopover(Gtk.Popover):
    __gtype_name__ = 'DtoolSearchPopover'

    search_text_view = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()

    def __init__(self, *args, search_entry : Gtk.SearchEntry, **kwargs):
        # on_show_clicked = kwargs.pop('on_show_clicked', None)
        super().__init__(*args, **kwargs)
        # if on_show_clicked is not None:
            # self.show_dataset_button.connect('clicked', on_show_clicked)

        self.search_entry = search_entry
        self.search_entry_buffer = self.search_entry.get_buffer()
        self.search_text_buffer = self.search_text_view.get_buffer()

        # set up some pseudo highlighting for the log window
        lang_manager = GtkSource.LanguageManager()
        self.search_text_buffer.set_language(lang_manager.get_language("json"))
        self.search_text_buffer.set_highlight_syntax(True)
        self.search_text_buffer.set_highlight_matching_brackets(True)

        self.set_relative_to(self.search_entry)
        self.search_entry.connect("button-press-event", self.on_search_entry_button_press)

    def popup_at(self, widget):
        search_text = self.search_entry_buffer.get_text()
        try:
            sanitized_search_text = multi_line_sanitize_query_text(search_text)
        except:
            logger.debug("Not a valid query.")
            sanitized_search_text = search_text
        self.search_text_buffer.set_text(sanitized_search_text, -1)

        self.set_relative_to(widget)
        logger.debug("Show search popover.")
        self.popup()

    def on_search_entry_button_press(self, widget, event):
        """"Display larger text box popover for multiline search queries on double-click in search bar."""
        if event.button == 1:
            logger.debug("Search entry clicked.")
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                logger.debug(f"Search entry double-clicked, show popover at {event.x, event.y}.")
                self.popup_at(widget)

    @Gtk.Template.Callback()
    def on_search_button_clicked(self, button):
        """"Update search bar text when clicking search button in search popover."""
        start_iter = self.search_text_buffer.get_start_iter()
        end_iter = self.search_text_buffer.get_end_iter()
        search_text = self.search_text_buffer.get_text(start_iter, end_iter, True)
        try:
            sanitized_search_text = single_line_sanitize_query_text(search_text)
        except:
            logger.debug("Not a valid query.")
            sanitized_search_text = search_text
        self.search_entry_buffer.set_text(sanitized_search_text, -1)
        self.popdown()
        self.get_action_group("win").activate_action('search-select-show', GLib.Variant.new_string(sanitized_search_text))

    @Gtk.Template.Callback()
    def on_cancel_button_clicked(self, button):
        self.popdown()
