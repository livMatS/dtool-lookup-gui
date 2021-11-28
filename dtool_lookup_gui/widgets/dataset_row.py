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

from dtool_info.utils import date_fmt


class DtoolDatasetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolDatasetRow'

    _margin = 3

    def __init__(self, dataset, *args, **kwargs):
        self._dataset = dataset

        super().__init__(*args, **kwargs)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        label = Gtk.Label(xalign=0)
        if dataset.is_frozen:
            label.set_markup(f'<b>{dataset.uuid}</b>')
        else:
            label.set_markup(f'<b>* {dataset.uuid}</b>')
        vbox.pack_start(label, True, True, 0)
        label = Gtk.Label(xalign=0)
        label.set_markup(f'{dataset.name}')
        vbox.pack_start(label, True, True, 0)
        label = Gtk.Label(xalign=0)
        label.set_markup(
            f'<small>Created by {dataset.creator}, ' +
            (f'frozen at {dataset.date}, {dataset.size_str.strip()}' if dataset.is_frozen else 'not yet frozen') +
            f'</small>')
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)

    @property
    def dataset(self):
        return self._dataset