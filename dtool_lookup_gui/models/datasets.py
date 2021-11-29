#
# Copyright 2021 Johannes Hoermann, Lars Pastewka
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import logging
import yaml

import dtoolcore
from dtoolcore.utils import generous_parse_uri
from dtool_info.utils import date_fmt, sizeof_fmt

from dtool_info.inventory import _dataset_info
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

logger = logging.getLogger(__name__)


def _proto_dataset_info(dataset):
    """Return information about proto dataset as a dict."""
    # Analogous to dtool_info.inventory._dataset_info
    info = {}

    info['uri'] = dataset.uri
    info['uuid'] = dataset.uuid

    info["size_int"] = None
    info["size_str"] = 'unknown'

    info['creator'] = dataset._admin_metadata['creator_username']
    info['name'] = dataset._admin_metadata['name']

    info["date"] = 'not yet frozen'

    info['readme_content'] = dataset.get_readme_content()

    return info


def _info(dataset):
    if isinstance(dataset, dtoolcore.DataSet):
        return _dataset_info(dataset)
    else:
        return _proto_dataset_info(dataset)


def _lookup_info(lookup_dict):
    """Mangle return dict of lookup server into a proper dataset info"""

    info = {}

    info['uri'] = lookup_dict['uri']
    info['uuid'] = lookup_dict['uuid']

    info["size_int"] = lookup_dict['size_in_bytes']
    info["size_str"] = sizeof_fmt(lookup_dict['size_in_bytes'])

    info['creator'] = lookup_dict['creator_username']
    info['name'] = lookup_dict['name']

    info['date'] = date_fmt(lookup_dict['frozen_at'])

    return info


def _mangle_lookup_manifest(manifest_dict):
    """Convert dictionary returned from lookup server into a normalized manifest"""
    manifest = []
    for key, value in manifest_dict['items'].items():
        manifest += [(key, value)]
    return manifest


class DatasetModel:
    """
    Model for both frozen and proto datasets, either received from dtoolcore
    or the lookup server.
    """

    _lookup_client = ConfigurationBasedLookupClient()

    @staticmethod
    def all(base_uri):
        """Return all datasets at base URI"""
        datasets = []
        for dataset in dtoolcore.iter_proto_datasets_in_base_uri(base_uri):
            datasets += [DatasetModel(dataset=dataset, base_uri=base_uri)]

        for dataset in dtoolcore.iter_datasets_in_base_uri(base_uri):
            datasets += [DatasetModel(dataset=dataset, base_uri=base_uri)]

        return datasets

    def __init__(self, uri=None, dataset=None, lookup_info=None, base_uri=None):
        self._base_uri = base_uri
        if uri is not None:
            if dataset is not None:
                raise ValueError('Please provide either `uri`, `dataset` or `lookup_info` arguments.')
            self._load_dataset(uri)
            self._dataset_info = _info(self._dataset)
        elif dataset is not None:
            self._dataset = dataset
            self._dataset_info = _info(self._dataset)
        elif lookup_info is not None:
            self._dataset = None
            self._dataset_info = _lookup_info(lookup_info)
        self._uri = generous_parse_uri(self._dataset_info['uri'])

    @classmethod
    async def search(cls, keyword):
        datasets = await cls._lookup_client.search(keyword)
        return [cls(lookup_info=dataset) for dataset in datasets]

    def __str__(self):
        return self._dataset.uri

    def __getattr__(self, name):
        return self.dataset_info[name]

    def _load_dataset(self, uri):
        """Load the dataset from a URI.

        :param uri: URI to a dtoolcore.DataSet
        """
        logger.info('{} loading dataset from URI: {}'.format(self, uri))
        self.clear()

        # determine from admin metadata whether this is a protodataset
        admin_metadata = dtoolcore._admin_metadata_from_uri(uri, None)

        if admin_metadata['type'] == 'protodataset':
            self._dataset = dtoolcore.ProtoDataSet.from_uri(uri)
        else:
            self._dataset = dtoolcore.DataSet.from_uri(uri)

    def reload(self):
        uri = self.dataset.uri
        self.clear()
        self._load_dataset(uri)

    @property
    def base_uri(self):
        return self._base_uri

    @property
    def scheme(self):
        return self._uri.scheme

    @property
    def is_frozen(self):
        return self._dataset is None or isinstance(self._dataset, dtoolcore.DataSet)

    @property
    def dataset(self):
        return self._dataset

    @property
    def dataset_info(self):
        return self._dataset_info

    @property
    def has_dependencies(self):
        return self.dataset is None

    def freeze(self):
        return self._dataset.freeze()

    def put_readme(self, text):
        self.dataset_info['readme_content'] = text
        return self._dataset.put_readme(text)

    async def readme(self):
        if 'readme_content' in self.dataset_info:
            return self.dataset_info['readme_content']
        else:
            readme_dict = await self._lookup_client.readme(self.uri)
            return yaml.dump(readme_dict)

    async def manifest(self):
        if self.dataset is not None:
            # Construct manifest from dtool dataset
            manifest = []
            if self.is_frozen:
                for identifier in self.dataset._identifiers():
                    manifest += [(identifier, self.dataset.item_properties(identifier))]
        else:
            # Query manifest from lookup server
            manifest_dict = await self._lookup_client.manifest(self.uri)
            manifest = _mangle_lookup_manifest(manifest_dict)
        return manifest

