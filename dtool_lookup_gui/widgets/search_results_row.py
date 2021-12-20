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

from gi.repository import Gtk


class DtoolSearchResultsRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolSearchResultsRow'

    _margin = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._task = None
        self._search_results = None

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        image = Gtk.Image.new_from_icon_name('edit-find-symbolic', Gtk.IconSize.BUTTON)
        image.set_padding(12, 12)
        hbox.pack_start(image, False, False, 0)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(xalign=0)
        label.set_markup(f'<b>Lookup server</b>')
        vbox.pack_start(label, True, True, 0)
        self._info_label = Gtk.Label(xalign=0)
        self._info_label.set_text('---')
        vbox.pack_start(self._info_label, True, True, 0)
        hbox.pack_start(vbox, True, True, 0)
        self._spinner = Gtk.Spinner(margin_top=self._margin, margin_bottom=self._margin,
                                    margin_start=self._margin, margin_end=self._margin)
        hbox.pack_start(self._spinner, False, False, 0)
        self.add(hbox)

    @property
    def search_results(self):
        return self._search_results

    @search_results.setter
    def search_results(self, search_results):
        self._search_results = search_results

    @property
    def info_label(self):
        return self._info_label

    def start_spinner(self):
        self._spinner.start()

    def stop_spinner(self):
        self._spinner.stop()

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, task):
        self._task = task
