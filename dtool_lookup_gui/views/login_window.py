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

# Define the LoginWindow class and associate it with its corresponding UI file
@Gtk.Template(filename=f'{os.path.dirname(__file__)}/login_window.ui')
class LoginWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'LoginWindow'

    # Map GTK Template Child widgets to Python attributes
    username_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    login_button = Gtk.Template.Child()
    skip_button = Gtk.Template.Child()
    settings_button = Gtk.Template.Child()

    # Initialize the LoginWindow instance
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = self.get_application()
        self.settings_dialog = SettingsDialog(application=self.application)

    # Handle the 'Login' button click event
    @Gtk.Template.Callback()
    def on_login_button_clicked(self, widget):
        # Import MainWindow class to create an instance after successful login
        from .main_window import MainWindow

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

        # Create and display the main window
        main_win = MainWindow(application=self.get_application())
        main_win.show()

        # Trigger the 'refresh-view' action in the main window
        action_group = main_win.get_action_group("win")
        if action_group:
            action_group.activate_action('refresh-view', None)

        # Close the login window
        self.close()

    # Handle the 'Skip' button click event
    @Gtk.Template.Callback()
    def on_skip_button_clicked(self, widget):
        # Import MainWindow to switch to it when 'Skip' is clicked
        from .main_window import MainWindow

        # Create and display the main window
        main_win = MainWindow(application=self.get_application())
        main_win.show()

        # Trigger the 'refresh-view' action in the main window
        action_group = main_win.get_action_group("win")
        if action_group:
            action_group.activate_action('refresh-view', None)

        # Close the login window
        self.close()

    @Gtk.Template.Callback()
    def settings_button_clicked_cb(self, widget):
        logger.info("Settings button clicked. Opening settings dialog.")
        self.settings_dialog.show()

    # Handle the window close event
    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        # Hide the window instead of deleting it
        return self.hide_on_delete()


