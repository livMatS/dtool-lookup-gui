#
# Copyright 2021 Lars Pastewka
#           2021 Johannes Hörmann
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
import logging
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource

import gbulb
gbulb.install(gtk=True)

from .views.main_window import MainWindow

# The following imports are need to register widget types with the GObject type system
import dtool_lookup_gui.widgets.base_uri_list_box
import dtool_lookup_gui.widgets.dataset_list_box
import dtool_lookup_gui.widgets.graph_widget
import dtool_lookup_gui.widgets.transfer_popover_menu
import dtool_lookup_gui.widgets.progress_chart
import dtool_lookup_gui.widgets.progress_popover_menu


logger = logging.getLogger(__name__)


# adapted from https://python-gtk-3-tutorial.readthedocs.io/en/latest/popover.html#menu-popover
class Application(Gtk.Application):
    def __init__(self, *args, loop=None, **kwargs):
        super().__init__(*args,
                         application_id='de.uni-freiburg.dtool-lookup-gui',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.loop = loop
        self.args = None

    def do_activate(self):
        logger.debug("do_activate")
        win = self.props.active_window
        if not win:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            # self.window = AppWindow(application=self, title="Main Window")
            logger.debug("Build GUI.")

            win = MainWindow(application=self)
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

        # parse the command line stored in args, but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])

        loglevel = logging.WARNING

        if self.args.quiet:
            loglevel = logging.ERROR
        if self.args.verbose > 0:
            loglevel = logging.INFO
        if self.args.debug or (self.args.verbose > 1):
            loglevel = logging.DEBUG

        # explicitly modify the root logger
        logging.basicConfig(level=loglevel)
        self.activate_action('set-loglevel', GLib.Variant.new_uint16(loglevel))

        logger.debug("Parsed CLI options {}".format(self.args))

        self.activate()
        return 0

    def do_startup(self):
        """Runs before anything else, create custom actions here."""
        logger.debug("do_startup")

        root_logger = logging.getLogger()

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
        if action.get_state().get_uint16() == value.get_uint16():
            logger.debug("Desired loglevel and current log level are equivalent.")
            return
        action.set_state(value)
        root_logger = logging.getLogger()
        root_logger.setLevel(value.get_uint16())

def run_gui():
    GObject.type_register(GtkSource.View)

    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    logger.debug("do_startup")
    # see https://github.com/beeware/gbulb#gapplicationgtkapplication-event-loop
    loop.run_forever(application=app, argv=sys.argv)

