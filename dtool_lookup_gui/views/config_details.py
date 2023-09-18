import asyncio
import logging
import os
import gi


gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango
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

        # Create the "bold" tag for the buffer
        buffer = self.config_text_view.get_buffer()
        tag_bold = buffer.create_tag("bold", weight=Pango.Weight.BOLD)

    async def _retrieve_config(self):
        """Asynchronously fetch server configuration and update the text view."""
        server_config = await config()
        config_info = self._format_server_config(server_config)
        _log_nested(logger.info, config_info)
        buffer = self.config_text_view.get_buffer()
        buffer.set_text("")  # Clearing the buffer
        buffer.insert_at_cursor("\n".join(config_info))
        self._apply_bold_to_buffer(buffer)

    def _apply_bold_to_buffer(self, buffer):
        """Apply bold style where '**' are present."""
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        start = 0

        while True:
            start_pos = text.find("**", start)
            if start_pos == -1:
                break
            end_pos = text.find("**", start_pos + 2)
            if end_pos == -1:
                break

            start_mark = buffer.create_mark(None, buffer.get_iter_at_offset(start_pos), True)
            end_mark = buffer.create_mark(None, buffer.get_iter_at_offset(end_pos), True)

            buffer.apply_tag_by_name("bold", buffer.get_iter_at_mark(start_mark), buffer.get_iter_at_mark(end_mark))
            buffer.delete(buffer.get_iter_at_mark(end_mark), buffer.get_iter_at_offset(end_pos + 2))
            buffer.delete(buffer.get_iter_at_mark(start_mark), buffer.get_iter_at_offset(start_pos + 2))

            # Removing marks after their use
            buffer.delete_mark(start_mark)
            buffer.delete_mark(end_mark)

            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            start = start_pos + 1

    def _format_server_config(self, server_config, indent=0):
        """Format the server configuration into a string representation for Markdown."""
        markdown_lines = []
        indentation = '    ' * indent  # 4 spaces per indentation level

        if not isinstance(server_config, dict):
            return [f"{indentation}- {server_config}"]

        for key, value in server_config.items():
            # If value is a dictionary, recurse with increased indentation
            if isinstance(value, dict):
                markdown_lines.append(f"{indentation}**{key}**:")
                markdown_lines.extend(self._format_server_config(value, indent + 1))
            # If value is a list, handle it by enumerating its items
            elif isinstance(value, list):
                markdown_lines.append(f"{indentation}**{key}**:")
                for item in value:
                    if isinstance(item, (dict, list)):
                        markdown_lines.extend(self._format_server_config(item, indent + 1))
                    else:
                        markdown_lines.append(f"{indentation}- {item}")
            # For simple key-value pairs
            else:
                markdown_lines.append(f"{indentation}**{key}**: {value}")

        return markdown_lines

    @Gtk.Template.Callback()
    def on_config_show(self, widget):
        """Callback executed when the window is shown; fetches server config."""
        asyncio.create_task(self._retrieve_config())

    @Gtk.Template.Callback()
    def on_config_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()

