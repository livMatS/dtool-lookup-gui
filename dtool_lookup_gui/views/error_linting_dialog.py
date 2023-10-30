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