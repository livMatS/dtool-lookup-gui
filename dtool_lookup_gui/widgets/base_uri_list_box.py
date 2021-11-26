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

from gi.repository import GObject, Gtk

from ..models.base_uris import all as all_base_uris
from .base_uri_row import DtoolBaseURIRow
from .search_results_row import DtoolSearchResultsRow


class DtoolBaseURIListBox(Gtk.ListBox):
    __gtype_name__ = 'DtoolBaseURIListBox'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._search_results_row = None

    def refresh(self, on_activate=None):
        for row in self.get_children():
            row.destroy()
        self._search_results_row = DtoolSearchResultsRow()
        self.add(self.search_results_row)
        base_uris = all_base_uris()
        for base_uri in base_uris:
            self.add(DtoolBaseURIRow(base_uri, on_activate=on_activate))
        self.show_all()

    def select_search_results_row(self):
        if self._search_results_row is not None:
            self.select_row(self._search_results_row)

    @property
    def search_results_row(self):
        return self._search_results_row


GObject.type_register(DtoolBaseURIListBox)