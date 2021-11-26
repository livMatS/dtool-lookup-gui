#
# Copyright 2021 Lars Pastewka, Johanns Hoermann
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

from gi.repository import Gtk


class DtoolBaseURIRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolBaseURIRow'

    _margin = 3

    def __init__(self, base_uri, *args, **kwargs):
        self.base_uri = base_uri
        on_activate = kwargs.pop('on_activate', None)
        on_configure = kwargs.pop('on_configure', None)

        super().__init__(*args, **kwargs)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        image = Gtk.Image.new_from_icon_name('network-server-symbolic', Gtk.IconSize.BUTTON)
        hbox.pack_start(image, True, True, 0)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(xalign=0)
        label.set_markup(str(base_uri))
        vbox.pack_start(label, True, True, 0)
        label = Gtk.Label(xalign=0)
        #if info['local'] and info['remote']:
        #    label.set_markup('This endpoint is reported by the lookup server and it is configured locally.')
        #elif not info['local'] and info['remote']:
        #    label.set_markup('This endpoint is reported by the lookup server, but it is not configured locally.')
        #else:
        #    label.set_markup('This endpoint is configured locally.')
        vbox.pack_start(label, True, True, 0)
        hbox.pack_start(vbox, True, True, 0)
        if on_configure is not None:
            button = Gtk.Button(image=Gtk.Image.new_from_icon_name('emblem-system-symbolic', Gtk.IconSize.BUTTON))
            button.connect('clicked', on_configure)
            # We currently can only configure S3 endpoints through the GUI
            #button.set_sensitive(parsed_uri.scheme == 's3')
            #button.base_uri = parsed_uri
            hbox.pack_end(button, False, False, 0)
        self.add(hbox)

        if on_activate is not None:
            self.connect('activate', on_activate)