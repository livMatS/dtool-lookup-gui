#
# Copyright 2022 Johannes Laurin Hörmann
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

import logging

from gi.repository import GObject, Gtk

from ..models.base_uris import all, LocalBaseURIModel
from .base_uri_row import DtoolBaseURIRow
from .search_results_row import DtoolSearchResultsRow


logger = logging.getLogger(__name__)


LOOKUP_BASE_URI = 'lookup://search'


class DtoolBaseURIListBox(Gtk.ListBox):
    __gtype_name__ = 'DtoolBaseURIListBox'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._search_results_row = None
        self._uri_to_row_index_mapping = dict()

    def add(self, row):
        """Keep uri -> row index mapping up-to-date."""

        # TODO: more elegant distinction between base URI and search rows
        if isinstance(row, DtoolBaseURIRow):
            base_uri = str(row.base_uri)
        else:
            base_uri = LOOKUP_BASE_URI

        if isinstance(row, DtoolBaseURIRow) and base_uri in self._uri_to_row_index_mapping:
            row_index = self.get_row_index_from_uri(base_uri)
            raise ValueError(f"{base_uri} already in DtoolBaseURIListBox at index {row_index}. This should not happen.")

        super().add(row)

        row_index = row.get_index()
        logger.debug(f"Inserted '{base_uri}' at {row_index}.")
        self._uri_to_row_index_mapping[base_uri] = row_index

    def remove(self, row):
        """Keep uri -> row index mapping up-to-date."""
        if isinstance(row, DtoolBaseURIRow):
            base_uri = str(row.base_uri)
        else:
            base_uri = LOOKUP_BASE_URI

        if isinstance(row, DtoolBaseURIRow) and base_uri not in self._uri_to_row_index_mapping:
            raise ValueError(
                f"{base_uri} not recorded in DtoolBaseURIListBox uri -> row index mapping. This should not happen.")
        else:
            del self._uri_to_row_index_mapping[base_uri]

        super().remove(row)

    def get_row_index_from_uri(self, uri):
        if uri in self._uri_to_row_index_mapping:
            return self._uri_to_row_index_mapping[uri]
        else:
            logger.warning(f"{uri} not in DtoolBaseURIListBox.")
            return None

    async def refresh(self, on_activate=None, on_configure=None, local=True, lookup=None, search_results=True):
        for row in self.get_children():
            self.remove(row)
            row.destroy()
        if search_results:
            self._search_results_row = DtoolSearchResultsRow()
            self.add(self.search_results_row)
        base_uris = await all(local=local, lookup=lookup)
        for base_uri in base_uris:
            if base_uri.scheme == 'file':
                self.add(DtoolBaseURIRow(base_uri, on_activate=on_activate, on_configure=on_configure,
                                         on_remove=self.on_remove))
            else:
                self.add(DtoolBaseURIRow(base_uri, on_activate=on_activate, on_configure=on_configure))
        self.show_all()

    def select_search_results_row(self):
        if self._search_results_row is not None:
            self.select_row(self._search_results_row)

    def on_remove(self, button):
        row = button.get_parent().get_parent()
        LocalBaseURIModel.remove(row.base_uri)
        row.destroy()

    @property
    def search_results_row(self):
        return self._search_results_row


GObject.type_register(DtoolBaseURIListBox)
