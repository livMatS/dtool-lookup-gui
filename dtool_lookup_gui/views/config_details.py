import asyncio
import logging
import os
import json
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
    config_text_view = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _retrieve_config(self):
        """Asynchronously fetch server configuration and update the text view."""
        server_config = await config()
        config_info = self._format_server_config(server_config)
        _log_nested(logger.info, config_info)
        buffer = self.config_text_view.get_buffer()
        buffer.set_text(config_info)

    def _format_server_config(self, server_config):
        """Format the server configuration into a string representation."""
        return json.dumps(server_config, indent=4)

    @Gtk.Template.Callback()
    def on_config_show(self, widget):
        """Callback executed when the window is shown; fetches server config."""
        asyncio.create_task(self._retrieve_config())

    @Gtk.Template.Callback()
    def on_config_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()

