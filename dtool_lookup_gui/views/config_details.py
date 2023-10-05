import asyncio
import logging
import os
import gi
import json

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from dtool_lookup_api.asynchronous import config

# Set up logger for this module
logger = logging.getLogger(__name__)

@Gtk.Template(filename=f'{os.path.dirname(__file__)}/config_details.ui')
class ConfigDialog(Gtk.Window):
    __gtype_name__ = 'ConfigDialog'
    config_text_view = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setting margins for better spacing
        self.config_text_view.set_left_margin(30)
        self.config_text_view.set_right_margin(10)
        self.config_text_view.set_top_margin(5)
        self.config_text_view.set_bottom_margin(5)

    async def _retrieve_config(self):
        """Asynchronously fetch server configuration and update the text view."""
        server_config = await config()
        config_info = self._format_server_config(server_config)
        buffer = self.config_text_view.get_buffer()
        buffer.set_text("")  # Clearing the buffer
        buffer.insert_at_cursor("\n".join(config_info))

    def _format_server_config(self, server_config, indent=0):
        """Format the server configuration into a human-readable string representation."""
        formatted_lines = []

        if isinstance(server_config, dict):
            for key, value in server_config.items():
                if isinstance(value, dict):
                    formatted_lines.append(f"{key}:")
                    for inner_key, inner_value in value.items():
                        if isinstance(inner_value, dict):
                            formatted_lines.append(f"{inner_key}:")
                            for deep_key, deep_value in inner_value.items():
                                formatted_lines.append(f"{deep_key}:{deep_value}")
                        else:
                            formatted_lines.append(f"{inner_key}:{inner_value}")
                else:
                    formatted_lines.append(f"{key}:{value}")

        elif isinstance(server_config, list):
            for item in server_config:
                formatted_lines.append(f"- {item}")

        else:
            formatted_lines.append(str(server_config))

        return formatted_lines

    @Gtk.Template.Callback()
    def on_config_show(self, widget):
        """Callback executed when the window is shown; fetches server config."""
        asyncio.create_task(self._retrieve_config())

    @Gtk.Template.Callback()
    def on_config_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()
