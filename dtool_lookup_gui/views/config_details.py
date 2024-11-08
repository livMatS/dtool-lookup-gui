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
import asyncio
import logging
import os
import gi
import json

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from dtool_lookup_api.asynchronous import get_config

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
        server_config = await get_config()
        config_info = self._format_server_config(server_config)
        buffer = self.config_text_view.get_buffer()
        buffer.set_text("")  # Clearing the buffer
        buffer.insert_at_cursor("\n".join(config_info))

    def _format_server_config(self, server_config):
        """Format the server configuration into a human-readable string representation using json.dumps."""
        formatted_config = json.dumps(server_config, indent=4)
        return formatted_config.splitlines()

    @Gtk.Template.Callback()
    def on_config_show(self, widget):
        """Callback executed when the window is shown; fetches server config."""
        asyncio.create_task(self._retrieve_config())

    @Gtk.Template.Callback()
    def on_config_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()
