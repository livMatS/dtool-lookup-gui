#
# Copyright 2021 Lars Pastewka
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

from gi.repository import GObject, Gtk


class DtoolTransferPopoverMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'DtoolTransferPopoverMenu'

    _margin = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=self._margin, margin_bottom=self._margin,
                            margin_start=self._margin, margin_end=self._margin)
        self.add(self.vbox)

    def update(self, destinations, on_copy=None):
        for child in self.vbox.get_children():
            child.destroy()
        label = Gtk.Label(xalign=0, margin_top=self._margin, margin_bottom=self._margin)
        self.vbox.pack_start(label, True, False, 0)
        label.set_markup('<b>Select destination</b>')
        for destination in destinations:
            button = Gtk.ModelButton(text=destination)
            self.vbox.pack_start(button, True, False, 0)
            button.destination = destination
            if on_copy is not None:
                button.connect('clicked', on_copy)
        for child in self.get_children():
            child.show_all()


GObject.type_register(DtoolTransferPopoverMenu)
