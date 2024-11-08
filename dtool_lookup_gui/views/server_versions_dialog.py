#
# Copyright 2023 Ashwin Vazhappilly
#           2023 Johannes Laurin Hörmann
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

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from dtool_lookup_api.asynchronous import get_versions
from ..utils.logging import _log_nested

# Set up logger for this module
logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/server_versions_dialog.ui')
class ServerVersionsDialog(Gtk.Window):
    __gtype_name__ = 'ServerVersionsDialog'
    server_versions_label = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply margins to the server versions label for better aesthetics
        self.server_versions_label.set_margin_start(10)
        self.server_versions_label.set_margin_end(10)
        self.server_versions_label.set_margin_top(10)
        self.server_versions_label.set_margin_bottom(10)

    async def _retrieve_versions(self):
        """Asynchronously fetch server versions and update the label with formatted information."""
        server_versions = await get_versions()
        version_info = self._format_server_versions(server_versions)
        _log_nested(logger.info, version_info)
        self.server_versions_label.set_markup(version_info)

    def _format_server_versions(self, server_versions):
        """Format server versions, sorting components by name length."""
        sorted_components = sorted(server_versions.keys(), key=len)

        # Use list comprehension for concise formatting of server versions
        formatted_versions = [f"{component}: <b>{server_versions[component]}</b>" for component in sorted_components]
        return "\n".join(formatted_versions)

    @Gtk.Template.Callback()
    def on_show(self, widget):
        """Callback executed when the window is shown; fetches server versions."""
        asyncio.create_task(self._retrieve_versions())

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        """Callback executed when window close event is triggered; hides the window instead of deleting."""
        return self.hide_on_delete()
