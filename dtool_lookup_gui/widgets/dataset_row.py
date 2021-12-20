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

from gi.repository import Gtk

from dtool_info.utils import date_fmt


class DtoolDatasetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolDatasetRow'

    _margin = 3

    def __init__(self, dataset, *args, **kwargs):
        self._dataset = dataset

        super().__init__(*args, **kwargs)

        self._build()

    def _build(self):
        # Clear current contents
        for child in self.get_children():
            child.destroy()

        # Update row contents
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        self.uuid_label = Gtk.Label(xalign=0)
        vbox.pack_start(self.uuid_label, True, True, 0)
        self.name_label = Gtk.Label(xalign=0)
        vbox.pack_start(self.name_label, True, True, 0)
        self.info_label = Gtk.Label(xalign=0)
        vbox.pack_start(self.info_label, True, True, 0)
        self.add(vbox)

        self._refresh()

    def _refresh(self):
        if self._dataset.is_frozen:
            self.uuid_label.set_markup(f'<b>{self._dataset.uuid}</b>')
        else:
            self.uuid_label.set_markup(f'<b>* {self._dataset.uuid}</b>')
        self.name_label.set_markup(f'{self._dataset.name}')
        self.info_label.set_markup(
            f'<small>Created by {self._dataset.creator}, ' +
            (f'frozen at {self._dataset.date}, {self._dataset.size_str.strip()}'
             if self._dataset.is_frozen else 'not yet frozen') +
            f'</small>')

    @property
    def dataset(self):
        return self._dataset

    def freeze(self):
        self._dataset.freeze()
        self._refresh()