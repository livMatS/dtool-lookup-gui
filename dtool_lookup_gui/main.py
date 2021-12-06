#
# Copyright 2020 Lars Pastewka, Johanns Hoermann
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
from gi.repository import GObject, Gio, Gtk, GtkSource

import gbulb
gbulb.install(gtk=True)

from .views.main_window import MainWindow

# The following import are need to register dtype with the GObject type system
import dtool_lookup_gui.widgets.base_uri_list_box
import dtool_lookup_gui.widgets.dataset_list_box
import dtool_lookup_gui.widgets.transfer_popover_menu
import dtool_lookup_gui.widgets.graph_widget


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

        # parse the command line stored in args, but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])

        loglevel = logging.ERROR

        if self.args.verbose > 0:
            loglevel = logging.WARN
        if self.args.verbose > 1:
            loglevel = logging.INFO
        if self.args.debug or (self.args.verbose > 2):
            loglevel = logging.DEBUG

        # explicitly modify the root logger
        logging.basicConfig(level=loglevel)
        logger = logging.getLogger()
        logger.setLevel(loglevel)
        logger = logging.getLogger(__name__) # override global logger after modifying logging settings

        logger.debug("Parsed CLI options {}".format(self.args))

        self.activate()
        return 0

    def do_startup(self):
        """Stub, runs before anything else, create custom actions here."""
        logger.debug("do_startup")
        Gtk.Application.do_startup(self)


def run_gui():
    GObject.type_register(GtkSource.View)

    loop = asyncio.get_event_loop()
    app = Application(loop=loop)
    logger.debug("do_startup")
    # see https://github.com/beeware/gbulb#gapplicationgtkapplication-event-loop
    loop.run_forever(application=app, argv=sys.argv)

