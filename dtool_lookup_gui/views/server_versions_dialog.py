import asyncio
import logging
import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from dtool_lookup_api.asynchronous import versions
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
        server_versions = await versions()
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
