#
# Copyright 2023 Ashwin Vazhappilly
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
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Set up logger for this module
logger = logging.getLogger(__name__)

@Gtk.Template(filename=f'{os.path.dirname(__file__)}/error_linting_dialog.ui')
class LintingErrorsDialog(Gtk.Window):
    __gtype_name__ = 'LintingErrorsDialog'
    config_text_view = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setting margins for better spacing
        self.config_text_view.set_left_margin(30)
        self.config_text_view.set_right_margin(10)
        self.config_text_view.set_top_margin(5)
        self.config_text_view.set_bottom_margin(5)

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        """Don't delete, just hide."""
        return self.hide_on_delete()

    def set_error_text(self, error_text):
        """Set the error text to the text view."""
        text_buffer = self.config_text_view.get_buffer()
        text_buffer.set_text(error_text)