#
# Copyright 2021-2022 Johannes Laurin Hörmann
#           2021 Lars Pastewka
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

import argparse
import asyncio
import glob
import json
import logging
import os
import sys

import dtoolcore
import dtool_lookup_api.core.config

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, GdkPixbuf

import gbulb
gbulb.install(gtk=True)

from .views.main_window import MainWindow

from .utils.logging import _log_nested

# The following imports are need to register widget types with the GObject type system
import dtool_lookup_gui.widgets.base_uri_list_box
import dtool_lookup_gui.widgets.dataset_list_box
import dtool_lookup_gui.widgets.graph_widget
import dtool_lookup_gui.widgets.transfer_popover_menu
import dtool_lookup_gui.widgets.progress_chart
import dtool_lookup_gui.widgets.progress_popover_menu


logger = logging.getLogger(__name__)

from . import __version__

appid = f'de.uni-freiburg.dtool-lookup-gui.{__version__}'

# Windows taskbar icons fix
try:
    from ctypes import windll  # Only exists on Windows.
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
except ImportError:
    pass


# adapted from https://python-gtk-3-tutorial.readthedocs.io/en/latest/popover.html#menu-popover
class Application(Gtk.Application):
    __gsignals__ = {
        'dtool-config-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, *args, loop=None, **kwargs):
        super().__init__(*args,
                         application_id='de.uni-freiburg.dtool-lookup-gui',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.loop = loop
        self.args = None

    def do_activate(self):
        logger.debug("do_activate")

        # https://pyinstaller.readthedocs.io/en/latest/runtime-information.html
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            logger.debug('running in a PyInstaller bundle')
        else:
            logger.debug('running in a normal Python process')

        win = self.props.active_window
        if not win:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            # self.window = AppWindow(application=self, title="Main Window")
            logger.debug("Build GUI.")

            win = MainWindow(application=self)
            glob_pattern = os.path.join(os.path.dirname(__file__), os.pardir, 'data','icons','*','dtool_logo_small.xpm')
            icon_file_list = glob.glob(glob_pattern)
            if len(icon_file_list) > 0:
                icon_list = [GdkPixbuf.Pixbuf.new_from_file(icon_file) for icon_file in icon_file_list]
                win.set_icon_list(icon_list)
                logger.debug("Loaded %d icons from:", len(icon_file_list))
                logger.debug("{}", icon_file_list)
            else:
                logger.warning("Could not load app icons.")
            win.connect('destroy', lambda _: self.loop.stop())
            self.loop.call_soon(win.refresh)  # Populate widgets after event loop starts

        logger.debug("Present main window.")
        win.present()

    # adapted from http://fedorarules.blogspot.com/2013/09/how-to-handle-command-line-options-in.html
    # and https://python-gtk-3-tutorial.readthedocs.io/en/latest/application.html#example
    def do_command_line(self, args):
        """Handle command line options from within Gtk Application.

        Gtk.Application command line handler called if
        Gio.ApplicationFlags.HANDLES_COMMAND_LINE set.
        Must call self.activate() to get the application up and running."""

        Gtk.Application.do_command_line(self, args)  # call the default commandline handler

        # in order to have both:
        # * preformatted help text and ...
        # * automatic display of defaults
        class ArgumentDefaultsAndRawDescriptionHelpFormatter(
            argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
            pass

        parser = argparse.ArgumentParser(prog=self.get_application_id(),
                                         description=__doc__,
                                         formatter_class=ArgumentDefaultsAndRawDescriptionHelpFormatter)

        parser.add_argument('--verbose', '-v', action='count', dest='verbose',
                            default=0, help='Make terminal output more verbose')
        parser.add_argument('--debug', action='store_true',
                            help='Print debug info')
        parser.add_argument('--quiet','-q', action='store_true',
                            help='Print debug info')
        parser.add_argument('--log', required=False, nargs='?', dest="log",
                            default=None, const='out.log', metavar='LOG',
                            help='Write out.log, optionally specify log file name')

        # parse the command line stored in args, but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])

        loglevel = logging.WARNING
        logformat = "%(levelname)s: %(message)s"
        if self.args.quiet:
            loglevel = logging.ERROR
        if self.args.verbose > 0:
            loglevel = logging.INFO
        if self.args.debug or (self.args.verbose > 1):
            loglevel = logging.DEBUG

        if self.args.verbose > 2:
            logformat = (
                "[%(asctime)s - pid %(process)d - thread id %(thread)d - %(funcName)s - %(pathname)s:%(lineno)s]"
                " %(levelname)s: %(message)s"
            )

        # explicitly modify the root logger
        logging.basicConfig(level=loglevel, format=logformat)

        self.activate_action('set-loglevel', GLib.Variant.new_uint16(loglevel))
        if self.args.log:
            self.activate_action('set-logfile', GLib.Variant.new_string(self.args.log))

        logger.debug("Parsed CLI options {}".format(self.args))

        self.activate()
        return 0

    def do_startup(self):
        """Runs before anything else, create custom actions here."""
        logger.debug("do_startup")

        root_logger = logging.getLogger()

        string_variant = GLib.Variant.new_string("dummy")

        # toggle-logging
        toggle_logging_variant = GLib.Variant.new_boolean(True)
        toggle_logging_action = Gio.SimpleAction.new_stateful(
            "toggle-logging", None, toggle_logging_variant
        )
        toggle_logging_action.connect("change-state", self.do_toggle_logging)
        self.add_action(toggle_logging_action)

        # set-loglevel
        loglevel_variant = GLib.Variant.new_uint16(root_logger.level)
        loglevel_action = Gio.SimpleAction.new_stateful(
            "set-loglevel", loglevel_variant.get_type(), loglevel_variant
        )
        loglevel_action.connect("change-state", self.do_set_loglevel)
        self.add_action(loglevel_action)

        # set-logfile
        logfile_variant = GLib.Variant.new_string('none')
        logfile_action = Gio.SimpleAction.new_stateful(
            "set-logfile", logfile_variant.get_type(), logfile_variant
        )
        logfile_action.connect("change-state", self.do_set_logfile)
        self.add_action(logfile_action)

        # reset-config action
        reset_config_action = Gio.SimpleAction.new("reset-config")
        reset_config_action.connect("activate", self.do_reset_config)
        self.add_action(reset_config_action)

        # import-config action
        import_config_action = Gio.SimpleAction.new("import-config", string_variant.get_type())
        import_config_action.connect("activate", self.do_import_config)
        self.add_action(import_config_action)

        # export-config action
        export_config_action = Gio.SimpleAction.new("export-config", string_variant.get_type())
        export_config_action.connect("activate", self.do_export_config)
        self.add_action(export_config_action)

        Gtk.Application.do_startup(self)

    # custom application-scoped actions
    def do_toggle_logging(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            logger.debug("Return to default logging configuration.")
            logging.disable(logging.NOTSET)
            logger.debug("Returned to default logging configuration.")

        else:
            logger.debug("Disable all logging below WARNING.")
            logging.disable(logging.WARNING)
            logger.debug("Disabled all logging below WARNING.")

    def do_set_loglevel(self, action, value):
        loglevel = value.get_uint16()
        if action.get_state().get_uint16() == loglevel:
            logger.debug("Desired loglevel and current log level are equivalent.")
            return
        root_logger = logging.getLogger()
        root_logger.setLevel(loglevel)
        action.set_state(value)

    def do_set_logfile(self, action, value):
        logfile = value.get_string()
        if action.get_state().get_string() == logfile:
            logger.debug(f"Desired log file {logfile} and current log file are equivalent.")
            return
        fh = logging.FileHandler(logfile)
        root_logger = logging.getLogger()
        fh.setLevel(root_logger.level)
        fh.setFormatter(root_logger.handlers[0].formatter)
        root_logger.addHandler(fh)
        action.set_state(value)

    # action handlers
    def do_reset_config(self, action, value):
        """Empties config. All settings lost."""
        fpath = dtoolcore.utils.DEFAULT_CONFIG_PATH
        logger.debug(f"Remove config file '{fpath}'.")
        try:
            os.remove(fpath)
        except FileNotFoundError as exc:
            logger.warning(str(exc))
        else:
            # reinitialize config object underlying dtool_lookup_api,
            # this must disappear here and move into dtool_lookup_api
            dtool_lookup_api.core.config.Config = dtool_lookup_api.core.config.DtoolLookupAPIConfig(interactive=False)
            self.emit('dtool-config-changed')

    def do_import_config(self, action, value):
        """Import config from file. No sanity checking."""
        config_file = value.get_string()
        logger.debug(f"Import config from '{config_file}':")
        with open(config_file, 'r') as f:
            config = json.load(f)
        _log_nested(logger.debug, config)
        for key, value in config.items():
            dtoolcore.utils.write_config_value_to_file(key, value)
        # reinitialize config object underlying dtool_lookup_api,
        # this must disappear here and move into dtool_lookup_api
        dtool_lookup_api.core.config.Config = dtool_lookup_api.core.config.DtoolLookupAPIConfig(interactive=False)
        self.emit('dtool-config-changed')

    def do_export_config(self, action, value):
        """Import config from file."""
        config_file = value.get_string()
        logger.debug(f"Export config to '{config_file}':")
        config = dtoolcore.utils._get_config_dict_from_file()
        _log_nested(logger.debug, config)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

    # object method handlers for own signals
    def do_dtool_config_changed(self):
        """Doesn't do anything, just documents how GTK calls this method
           first when emitting dtool-config-changed signal."""
        logger.debug("method handler for 'dtool-config-changed' called.")


def run_gui():
    GObject.type_register(GtkSource.View)

    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    logger.debug("do_startup")
    # see https://github.com/beeware/gbulb#gapplicationgtkapplication-event-loop
    loop.run_forever(application=app, argv=sys.argv)

