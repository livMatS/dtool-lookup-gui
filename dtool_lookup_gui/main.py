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

import asyncio
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


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='de.uni-freiburg.dtool-lookup-gui',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        loop = asyncio.get_event_loop()
        win.connect('destroy', lambda _: loop.stop())
        loop.call_soon(win.refresh)  # Populate widgets after event loop starts
        win.show()
        loop.run_forever()


def run_gui():
    GObject.type_register(GtkSource.View)

    app = Application()
    return app.run(sys.argv)
