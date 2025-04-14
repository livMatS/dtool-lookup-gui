from importlib.metadata import entry_points

# import gi
# gi.require_version('Gtk', '3.0')
# from gi.repository import Gtk
import sys
import logging

_logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self.plugins = {}

    def load_plugins(self):
        if sys.version_info >= (3, 8):
            from importlib.metadata import entry_points
            eps = entry_points()
            if sys.version_info >= (3, 10):
                entrypoints = eps.select(group="dtool.gui")
            else:
                entrypoints = eps.get("dtool.gui", [])
        else:
            from pkg_resources import iter_entry_points
            entrypoints = iter_entry_points("dtool.gui")

        for ep in entrypoints:
            logging.debug("Load plugin via entrypoint '%s'", ep.name)
            plugin_class = ep.load()
            logging.debug("Loaded plugin class type '%s'", plugin_class)
            plugin = plugin_class()
            self.plugins[ep.name] = plugin

    def activate_plugin(self, plugin_name, window):
        if plugin_name in self.plugins:
            logging.debug("Activate plugin '%s'", plugin_name)
            self.plugins[plugin_name].activate(window)
        else:
            logging.warning("No plugin named '%s'", plugin_name)

    def deactivate_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            logging.debug("Deactivate plugin '%s'", plugin_name)
            self.plugins[plugin_name].deactivate()
        else:
            logging.warning("No plugin named '%s'", plugin_name)


class BasePlugin:
    def __init__(self):
        self.name = "Base Plugin"

    def activate(self, window):
        pass

    def deactivate(self):
        pass
