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

import logging

from gi.repository import GObject, Gtk

from .dataset_row import DtoolDatasetRow


logger = logging.getLogger(__name__)

class DtoolDatasetListBox(Gtk.ListBox):
    __gtype_name__ = 'DtoolDatasetListBox'

    def __init__(self, *args, **kwargs):
        self._uri_to_row_index_mapping = dict()

    def fill(self, datasets, on_show=None):
        for row in self.get_children():
            row.destroy()
        self._uri_to_row_index_mapping = dict()
        for dataset in datasets:
            self.add(DtoolDatasetRow(dataset))
        self.show_all()
        if on_show is not None:
            on_show(datasets)

    def add_dataset(self, dataset):
        # Create row for new dataset
        row = DtoolDatasetRow(dataset)
        self.add(row)
        # Select new dataset
        self.select_row(row)

    def add(self, row):
        """Keep uri -> row index mapping up-to-date."""
        if row.dataset.uri in self._uri_to_row_index_mapping:
            row_index  = self.get_row_index_from_uri(row.dataset.uri)
            raise ValueError(f"{row.dataset.uri} already in DtoolDatasetListBox at index {row_index}. This should not happen.")

        super().add(row)

        row_index = row.get_index()
        logger.debug(f"Inserted {row.dataset.uri} at {row_index}.")
        self._uri_to_row_index_mapping[row.dataset.uri] = row_index

    def remove(self, row):
        """Keep uri -> row index mapping up-to-date."""
        if row.dataset.uri not in self._uri_to_row_index_mapping:
            raise ValueError(f"{row.dataset.uri} not recorded in DtoolDatasetListBox uri -> row index mapping. This should not happen.")
        else:
            del self._uri_to_row_index_mapping[row.dataset.uri]

        super().remove(row)

    def get_row_index_from_uri(self, uri):
        if uri in self._uri_to_row_index_mapping:
            return self._uri_to_row_index_mapping[uri]
        else:
            logger.warning(f"{uri} not in DtoolDatasetListBox.")
            return None


GObject.type_register(DtoolDatasetListBox)
