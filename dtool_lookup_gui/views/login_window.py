import logging
import os

import dtoolcore

from gi.repository import Gio, GLib, Gtk ,Gdk

from ..utils.about import pretty_version_text
from ..utils.logging import _log_nested

logger = logging.getLogger(__name__)

@Gtk.Template(filename=f'{os.path.dirname(__file__)}/login_window.ui')
class LoginWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'LoginWindow'


    username_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    login_button = Gtk.Template.Child()
    skip_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @Gtk.Template.Callback()
    def on_login_button_clicked(self, widget):
        """Handle the login button click."""
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()
        print(f"Username: {username}, Password: {password}")

    @Gtk.Template.Callback()
    def on_skip_button_clicked(self, widget):
        """Handle the skip button click."""
        print("Skip was clicked!")

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        """Don't delete, just hide."""
        return self.hide_on_delete()
