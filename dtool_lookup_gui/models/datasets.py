#
# Copyright 2021 Johannes Hoermann, Lars Pastewka
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

import dtoolcore

from dtool_info.inventory import _dataset_info
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

logger = logging.getLogger(__name__)

lookup_client = ConfigurationBasedLookupClient()


def _proto_dataset_info(dataset):
    """Return information about proto dataset as a dict."""
    # Analogous to dtool_info.inventory._dataset_info
    info = {}

    info["uri"] = dataset.uri
    info["uuid"] = dataset.uuid

    # Computer and human readable size of dataset.

    info["creator"] = dataset._admin_metadata["creator_username"]
    info["name"] = dataset._admin_metadata["name"]

    info["readme_content"] = dataset.get_readme_content()

    return info


class DatasetModel:
    """
    Model for both frozen and proto datasets, either received from dtoolcore
    or the lookup server.
    """

    @staticmethod
    def all(base_uri):
        """Return all datasets at base URI"""
        datasets = []
        for dataset in dtoolcore.iter_proto_datasets_in_base_uri(base_uri):
            datasets += [DatasetModel(dataset=dataset)]

        for dataset in dtoolcore.iter_datasets_in_base_uri(base_uri):
            datasets += [DatasetModel(dataset=dataset)]

        return datasets

    def __init__(self, uri=None, dataset=None):
        if uri is not None:
            if dataset is not None:
                raise ValueError('Please provide either `uri` or `dataset` arguments.')
            self._load_dataset(uri)
        elif dataset is not None:
            self._dataset = dataset

    def __getattr__(self, name):
        return self.dataset_info[name]

    def _load_dataset(self, uri):
        """Load the dataset from a URI.

        :param uri: URI to a dtoolcore.DataSet
        """
        logger.info("{} loading dataset from URI: {}".format(self, uri))
        self.clear()

        # determine from admin metadata whether this is a protodataset
        admin_metadata = dtoolcore._admin_metadata_from_uri(uri, None)

        if admin_metadata["type"] == "protodataset":
            self._dataset = dtoolcore.ProtoDataSet.from_uri(uri)
        else:
            self._dataset = dtoolcore.DataSet.from_uri(uri)

    def reload(self):
        uri = self.dataset.uri
        self.clear()
        self._load_dataset(uri)

    @property
    def is_frozen(self):
        return isinstance(self._dataset, dtoolcore.DataSet)

    @property
    def dataset(self):
        return self._dataset

    @property
    def dataset_info(self):
        if self.is_frozen:
            return _dataset_info(self._dataset)
        else:
            return _proto_dataset_info(self._dataset)

    @property
    def readme(self):
        return self.dataset_info['readme_content']

    @property
    def identifiers(self):
        return self.dataset.identifiers

    def item_properties(self, identifier):
        return self.dataset.item_properties(identifier)