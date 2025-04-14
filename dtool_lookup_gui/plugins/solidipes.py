import logging

import os
import shutil
import tempfile
import argparse
from solidipes.downloaders.dtool import DToolDownloader
from solidipes.mounters.cloud import mount
from solidipes.reports.web_report import WebReportSpawner

from dtool_lookup_gui.plugins import BasePlugin
from multiprocessing import Process
from gi.repository import Gio, GLib, Gtk


_logger = logging.getLogger(__name__)


class SolidipesPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Solidipes Plugin"
        self._window = None
        self._menu_button = None

    def activate(self, window):
        """Activate SolidipesPlugin."""
        self._window = window
        popover_menu = self._window.burger_menu

        # add action
        uri_variant = GLib.Variant.new_string('dummy')
        export_with_solidipes_action = Gio.SimpleAction.new("export-with-solidipes", uri_variant.get_type())
        export_with_solidipes_action.connect("activate", self.do_export_with_solidipes)
        self._window.add_action(export_with_solidipes_action)

        _logger.debug("Got popver menu: %s", popover_menu)
        if not popover_menu:
            _logger.warning("Could not find 'burger_menu' in UI definition.")
            return

        # Get the GtkBox inside the popover menu
        stack = popover_menu.get_child()
        _logger.debug("Got child of popver menu: %s", stack)
        if not isinstance(stack, Gtk.Stack):
            _logger.warning("Popover child is not a Gtk.Stack.")
            return

        box = stack.get_visible_child()
        _logger.debug("Got child of stack: %s", box)
        if not isinstance(box, Gtk.Box):
            _logger.warning("Popover child is not a Gtk.Box.")
            return

        # Create a new menu item (GtkModelButton)
        self._menu_button = Gtk.ModelButton()
        self._menu_button.set_label("Export with Solidipes")  # Text for the new menu item
        self._menu_button.set_visible(True)
        self._menu_button.set_can_focus(True)
        self._menu_button.connect("clicked", self.on_menu_item_clicked)

        # Add the new button to the box
        box.add(self._menu_button)

    def deactivate(self):
        if self._menu_button:
            parent = self._menu_button.get_parent()
            if parent:
                parent.remove(self._menu_button)  # Remove button from its parent container
            self._menu_button = None

    def on_menu_item_clicked(self, widget):
        print("Solidipes Plugin menu item clicked!")
        row = self._window.dataset_list_box.get_selected_row()
        uri = row.dataset.uri
        self._window.get_action_group("win").activate_action(
            'export-with-solidipes', GLib.Variant.new_string(uri))

    def do_export_with_solidipes(self, action, value):
        """Export a dtool dataset with solidipes"""
        uri = value.get_string()
        _logger.debug("Export '%s' with solidipes")

        # export_process = StatusReportingChildProcessBuilder(export_function, StatusHandler)
        export_process = Process(target=export_with_solidipes, args=(uri,))
        export_process.start()
        # asyncio.create_task(export_process(uri))
        # export_with_solidipes(uri)


def export_with_solidipes(uri):
    """Export a dtool dataset with solidipes."""

    temp_dir = tempfile.mkdtemp()
    _logger.debug(f"Created temporary directory: %s", temp_dir)

    # Store the current working directory
    original_dir = os.getcwd()
    _logger.debug(f"Original directory: %s", original_dir)

    _logger.debug("Download only metadata from '%s'", uri)
    args = argparse.Namespace(
        identifier=uri,
        destination=temp_dir,
        debug=True,
        subdir=None,
        only_metadata=True,
    )

    downloader = DToolDownloader()
    downloader.download(args)

    # Change into the temporary directory
    os.chdir(temp_dir)
    _logger.debug("Changed to temporary directory: %s", os.getcwd())

    mount(type="dtool", path="data", endpoint=uri)

    os.chdir(original_dir)

    # Launch web report
    _logger.debug(f"Launch web report on '%s'", temp_dir)
    args = argparse.Namespace(
        dir_path=temp_dir,
        debug=True,
        additional_arguments=[]
    )

    web_report = WebReportSpawner()
    web_report.make(args)

    # how to exit the web gui gracefully?

    shutil.rmtree(temp_dir)

    return 0
