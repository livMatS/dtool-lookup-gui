import asyncio
import logging
import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from dtool_lookup_api.asynchronous import config
from ..utils.logging import _log_nested

# Set up logger for this module
logger = logging.getLogger(__name__)

@Gtk.Template(filename=f'{os.path.dirname(__file__)}/config_details.ui')
class ConfigDialog(Gtk.Window):
    __gtype_name__ = 'ConfigDialog'
    config_label = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply margins to the config label for better aesthetics
        self.config_label.set_margin_start(10)
        self.config_label.set_margin_end(10)
        self.config_label.set_margin_top(10)
        self.config_label.set_margin_bottom(10)

    async def _retrieve_config(self):
        """Asynchronously fetch server configuration and update the label with the first key-value pair."""
        server_config = await config()
        config_info = self._format_server_config(server_config)
        _log_nested(logger.info, config_info)
        self.config_label.set_markup(config_info)

    def _format_server_config(self, server_config):
        """Format the first key-value pair from the server configuration."""
        first_key = next(iter(server_config))
        return f"{first_key}: <b>{server_config[first_key]}</b>"

    @Gtk.Template.Callback()
    def on_config_show(self, widget):
        """Callback executed when the window is shown; fetches server config."""
        asyncio.create_task(self._retrieve_config())

    @Gtk.Template.Callback()
    def on_config_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()
