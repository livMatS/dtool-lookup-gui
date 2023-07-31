import logging
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk

from ..utils.logging import _log_nested


logger = logging.getLogger(__name__)


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/server_versions_dialog.ui')
class ServerVersionsDialog(Gtk.Window):
    __gtype_name__ = 'ServerVersionsDialog'

    server_versions_label = Gtk.Template.Child()

    def __init__(self, server_versions, *args, **kwargs):
        super().__init__(*args, **kwargs)

        version_info = self._format_server_versions(server_versions)
        _log_nested(logger.info, version_info)
        self.server_versions_label.set_markup(version_info)

    def _format_server_versions(self, server_versions):
        # Just return a placeholder string instead of formatting actual data
        return "<b>Server Versions:</b>\nComponent1: 1.0\nComponent2: 2.0\n"

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        """Don't delete, just hide."""
        return self.hide_on_delete()
