#
# Copyright 2023 Johannes Laurin Hörmann
#           2023 Ashwin Vazhappilly
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
import dtoolcore
from gi.repository import Gio, GLib, Gtk, Gdk
from dtool_lookup_api.core.config import Config
from ..utils.about import pretty_version_text
from ..utils.logging import _log_nested
from .settings_dialog import SettingsDialog

# Initialize logging
logger = logging.getLogger(__name__)

@Gtk.Template(filename=f'{os.path.dirname(__file__)}/login_window.ui')
class LoginWindow(Gtk.Window):
    __gtype_name__ = 'LoginWindow'

    # Map GTK Template Child widgets to Python attributes
    username_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    login_button = Gtk.Template.Child()
    skip_button = Gtk.Template.Child()
    settings_button = Gtk.Template.Child()

    # Initialize the LoginWindow instance
    def __init__(self, follow_up_action=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = self.get_application()
        self.settings_dialog = SettingsDialog(application=self.application)
        self._follow_up_action = follow_up_action

        # Set the default values from the Config, ensuring they are not None
        if Config.username is not None:
            self.username_entry.set_text(Config.username)
        if Config.password is not None:  # Consider security implications
            self.password_entry.set_text(Config.password)

        self.username_entry.connect("activate", self.on_username_activate)
        self.password_entry.connect("activate", self.on_password_activate)

    def on_username_activate(self, entry):
        self.password_entry.grab_focus()

    def on_password_activate(self, entry):
        self.on_login_button_clicked(None)

    # Handle the 'Login' button click event
    @Gtk.Template.Callback()
    def on_login_button_clicked(self, widget):
        # Fetch entered username and password
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()

        # Create a GLib Variant tuple for authentication
        user_pass_auth_variant = GLib.Variant.new_tuple(
            GLib.Variant.new_string(username),
            GLib.Variant.new_string(password),
            GLib.Variant.new_string(Config.auth_url)
        )

        # Trigger the 'renew-token' action for authentication
        self.get_action_group("app").activate_action('renew-token', user_pass_auth_variant)

        if self._follow_up_action is not None:
            self._follow_up_action()

        self.close()

    # Handle the 'Skip' button click event
    @Gtk.Template.Callback()
    def on_skip_button_clicked(self, widget):
        # Close the login window
        self.close()

    @Gtk.Template.Callback()
    def on_settings_button_clicked_cb(self, widget):
        logger.info("Settings button clicked. Opening settings dialog.")
        self.settings_dialog.show()

    # Handle the window close event
    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        # Hide the window instead of deleting it
        return self.hide_on_delete()


