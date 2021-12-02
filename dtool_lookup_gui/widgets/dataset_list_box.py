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

import asyncio

from gi.repository import GObject, Gtk

from ..models.datasets import DatasetModel
from .dataset_row import DtoolDatasetRow


class DtoolDatasetListBox(Gtk.ListBox):
    __gtype_name__ = 'DtoolDatasetListBox'

    _max_nb_datasets = 100

    def fill(self, datasets, on_show=None):
        for row in self.get_children():
            row.destroy()
        for dataset in datasets:
            self.add(DtoolDatasetRow(dataset))
        self.show_all()
        if on_show is not None:
            on_show(datasets)

    async def from_base_uri(self, base_uri, on_show=None):
        self.fill(await base_uri.all_datasets(), on_show=on_show)

    def search(self, keyword, on_show=None, on_error=None):
        async def fetch_search_results(keyword, on_show=None):
            try:
                datasets = await DatasetModel.search(keyword)
                datasets = datasets[:self._max_nb_datasets]
                self.fill(datasets, on_show=on_show)
            except Exception as e:
                if on_error is not None:
                    on_error(e)
                else:
                    raise
        asyncio.create_task(fetch_search_results(keyword, on_show=on_show))

    def add_dataset(self, dataset):
        # Create row for new dataset
        row = DtoolDatasetRow(dataset)
        self.add(row)
        # Select new dataset
        self.select_row(row)

GObject.type_register(DtoolDatasetListBox)
