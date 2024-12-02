#
# Copyright 2021-2023 Johannes Laurin Hörmann
#           2023 Ashwin Vazhappilly
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
import ssl
import sys

import dtoolcore
import dtool_lookup_api.core.config

from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, GdkPixbuf
from gi.events import GLibEventLoopPolicy

from .models.settings import settings

from .views.main_window import MainWindow
from .views.login_window import LoginWindow

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

# APP_ID = f'de.uni-freiburg.dtool-lookup-gui.{__version__}'
APP_ID = 'de.uni-freiburg.dtool-lookup-gui'

# Windows taskbar icons fix
try:
    from ctypes import windll  # Only exists on Windows.
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
except ImportError:
    pass


# adapted from https://python-gtk-3-tutorial.readthedocs.io/en/latest/popover.html#menu-popover
class Application(Gtk.Application):
    __gsignals__ = {
        'dtool-config-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'token-renewed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'startup-done': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'activation-done': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, *args, loop=None,
                 application_id=APP_ID,
                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs):
        print("Launch with application_id %s" % application_id)
        super().__init__(*args,
                         application_id=application_id,
                         flags=flags, **kwargs)
        self.loop = loop
        self.args = None

        self._startup_done = asyncio.Event()
        self._activation_done = asyncio.Event()
        self._shutdown_done = asyncio.Event()

    async def shutdown(self):
        # Perform any cleanup tasks here
        for window in self.get_windows():
            window.close()
        self.quit()
        self._shutdown_done.set()

    def on_window_destroy(self, window):
        self.quit()
        # return False

    def on_startup_done(self, app):
        logger.debug("Received startup-done signal in on_startup_done signal handler.")
        self._startup_done.set()

    def on_activation_done(self, app):
        logger.debug("Received activation-done signal in on_activation_done signal handler.")
        self._activation_done.set()

    def on_shutdown(self, app):
        logger.debug("Received shutdown signal in on_shutdown signal handler.")
        self._shutdown_done.set()

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
            glob_pattern = os.path.join(os.path.dirname(__file__), os.pardir, 'data','icons','*','dtool_logo.xpm')
            icon_file_list = glob.glob(glob_pattern)
            if len(icon_file_list) > 0:
                icon_list = [GdkPixbuf.Pixbuf.new_from_file(icon_file) for icon_file in icon_file_list]
                win.set_icon_list(icon_list)
                logger.debug("Loaded %d icons from:", len(icon_file_list))
                logger.debug("%s", icon_file_list)
            else:
                logger.warning("Could not load app icons.")
            win.connect("destroy", self.on_window_destroy)
            self.loop.call_soon(win.refresh)  # Populate widgets after event loop starts

        logger.debug("Present main window.")
        win.present()
        self.emit('activation-done')

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

        # connect signals and signal handlers
        self.connect('startup-done', self.on_startup_done)
        self.connect('activation-done', self.on_activation_done)
        self.connect('shutdown', self.on_shutdown)

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

        # renew-token action
        renew_token_action = Gio.SimpleAction.new("renew-token", GLib.VariantType.new("(sss)"))
        renew_token_action.connect("activate", self.do_renew_token)
        self.add_action(renew_token_action)

        Gtk.Application.do_startup(self)

        self.emit('startup-done')


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
        logger.debug(f"Reset Gtk app settings.")
        settings.reset()

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

    def do_renew_token(self, action, value):
        """Request new token."""

        # Unpack the username, password, and auth_url from the tuple variant
        username, password, auth_url = value.unpack()

        logger.debug("look for certificates in %s", ssl.get_default_verify_paths())

        async def retrieve_token(auth_url, username, password):
            try:
                async with ConfigurationBasedLookupClient(
                        auth_url=auth_url, username=username, password=password) as lookup_client:
                    token = await lookup_client.authenticate()
            except Exception as e:
                logger.error(str(e))
                return

            dtool_lookup_api.core.config.Config.token = token
            self.emit("token-renewed")
            self.emit('dtool-config-changed')

        asyncio.create_task(retrieve_token(
            auth_url,
            username,
            password))


    async def wait_for_activation(self):
        logger.debug("Waiting for activation-done signal.")
        await self._activation_done.wait()

    async def wait_for_startup(self):
        logger.debug("Waiting for startup-done signal.")
        await self._startup_done.wait()

    async def wait_for_shutdown(self):
        logger.debug("Waiting for shutdown signal.")
        await self._shutdown_done.wait()


def run_gui():
    GObject.type_register(GtkSource.View)

    asyncio.set_event_loop_policy(GLibEventLoopPolicy())

    loop = asyncio.get_event_loop()
    app = Application(loop=loop)

    logger.debug("do_startup")
    app.run(sys.argv)

