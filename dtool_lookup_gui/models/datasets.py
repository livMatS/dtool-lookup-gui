#
# Copyright 2020-2021 Lars Pastewka
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

import asyncio
import logging
import os
import yaml
from concurrent.futures import ProcessPoolExecutor

import dtoolcore
from dtoolcore.utils import generous_parse_uri
from dtool_info.utils import date_fmt, sizeof_fmt

from dtool_info.inventory import _dataset_info
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

from ..utils.multiprocessing import StatusReportingChildProcessBuilder
from ..utils.progressbar import ProgressBar



logger = logging.getLogger(__name__)


def _proto_dataset_info(dataset):
    """Return information about proto dataset as a dict."""
    # Analogous to dtool_info.inventory._dataset_info
    info = {}

    info['type'] = 'dtool-proto'

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
        info = _dataset_info(dataset)
        info['type'] = 'dtool-dataset'
        info['is_frozen'] = True

        manifest = []
        for identifier in dataset._identifiers():
            manifest += [(identifier, dataset.item_properties(identifier))]
        info['manifest'] = manifest
    else:
        info = _proto_dataset_info(dataset)
        info['is_frozen'] = False

    p = generous_parse_uri(info['uri'])
    info['scheme'] = p.scheme
    info['base_uri'] = p.path if p.netloc is None else p.netloc

    return info


def _mangle_lookup_manifest(manifest_dict):
    """Convert dictionary returned from lookup server into a normalized manifest"""
    manifest = []
    for key, value in manifest_dict['items'].items():
        manifest += [(key, value)]
    return manifest


async def _lookup_info(lookup_dict):
    """Mangle return dict of lookup server into a proper dataset info"""

    info = {}

    uri = lookup_dict['uri']

    info['type'] = 'lookup'

    info['uri'] = uri
    p = generous_parse_uri(uri)
    info['scheme'] = p.scheme
    info['base_uri'] = p.path if p.netloc is None else p.netloc

    info['uuid'] = lookup_dict['uuid']

    # The server does not include these fields in response as of 0.17.2
    # They will be available in next release,
    # https://github.com/jic-dtool/dtool-lookup-server/pull/21
    try:
        info["size_int"] = lookup_dict['size_in_bytes']
        info["size_str"] = sizeof_fmt(lookup_dict['size_in_bytes'])
    except KeyError:
        info["size_int"] = None
        info["size_str"] = 'unknown'

    info['creator'] = lookup_dict['creator_username']
    info['name'] = lookup_dict['name']

    info['date'] = date_fmt(lookup_dict['frozen_at'])

    info['is_frozen'] = True

    return info


def _list_proto_datasets(base_uri):
    datasets = []
    for dataset in dtoolcore.iter_proto_datasets_in_base_uri(base_uri):
        datasets += [DatasetModel.from_dataset(dataset)]
    return datasets


def _list_datasets(base_uri):
    datasets = []
    for dataset in dtoolcore.iter_datasets_in_base_uri(base_uri):
        datasets += [DatasetModel.from_dataset(dataset)]
    return datasets


def _load_dataset(uri):
    logger.info(f'Loading dataset from URI: {uri}')

    # determine from admin metadata whether this is a protodataset
    admin_metadata = dtoolcore._admin_metadata_from_uri(uri, None)

    if admin_metadata['type'] == 'protodataset':
        dataset = dtoolcore.ProtoDataSet.from_uri(uri)
    else:
        dataset = dtoolcore.DataSet.from_uri(uri)

    return dataset


async def _copy_dataset(uri, target_base_uri, resume, auto_resume, progressbar=None):
    logger.info(f'Copying dataset from URI {uri} to {target_base_uri}...')

    dataset = _load_dataset(uri)

    dest_uri = dtoolcore._generate_uri(
        admin_metadata=dataset._admin_metadata,
        base_uri=target_base_uri
    )

    copy_func = dtoolcore.copy
    is_dataset = dtoolcore._is_dataset(dest_uri, config_path=None)
    if resume or (auto_resume and is_dataset):
        # copy resume
        copy_func = dtoolcore.copy_resume
    elif is_dataset:
        # don't resume
        raise FileExistsError("Dataset already exists: {}".format(dest_uri))
    else:
        # If the destination URI is a "file" dataset one needs to check if
        # the path already exists and exit gracefully if true.
        parsed_dataset_uri = dtoolcore.utils.generous_parse_uri(dest_uri)
        if parsed_dataset_uri.scheme == "file":
            if os.path.exists(parsed_dataset_uri.path):
                raise FileExistsError(
                    "Path already exists: {}".format(parsed_dataset_uri.path))

    num_items = len(list(dataset.identifiers))

    def copy_func_wrapper(src_uri, dest_base_uri, status_report_callback):
        copy_func(
            src_uri=src_uri,
            dest_base_uri=dest_base_uri,
            config_path=None,
            progressbar=status_report_callback,
        )

    with ProgressBar(length=num_items,
                     label="Copying dataset",
                     pb=progressbar) as pb:
        non_blocking_copy_func = StatusReportingChildProcessBuilder(copy_func_wrapper, pb)
        dest_uri = await non_blocking_copy_func(uri, target_base_uri)

    logger.info(f'Dataset successfully copied from {uri} to {target_base_uri}.')

    return dest_uri


class DatasetModel:
    """
    Model for both frozen and proto datasets, either received from dtoolcore
    or the lookup server.
    """

    @staticmethod
    async def all(base_uri):
        """Return all datasets at base URI"""

        datasets = []

        loop = asyncio.get_running_loop()
        datasets = []
        with ProcessPoolExecutor(2) as executor:
            datasets += await loop.run_in_executor(executor, _list_proto_datasets, base_uri)
            datasets += await loop.run_in_executor(executor, _list_datasets, base_uri)

        return datasets

    @classmethod
    def from_uri(cls, uri):
        return cls(uri=uri)

    @classmethod
    def from_dataset(cls, dataset):
        return cls(dataset_info=_info(dataset))

    @classmethod
    async def from_lookup(cls, lookup_dict):
        return cls(dataset_info=await _lookup_info(lookup_dict))

    def __init__(self, uri=None, dataset_info=None):
        if uri is not None:
            self.reload(uri)
        elif dataset_info is not None:
            self._dataset_info = dataset_info
        else:
            raise ValueError('Please provide either `uri` or `dateset_info`.')

    @classmethod
    async def search(cls, keyword):
        async with ConfigurationBasedLookupClient() as lookup:
            datasets = await lookup.search(keyword)

        return [await cls.from_lookup(lookup_dict) for lookup_dict in datasets]

    @classmethod
    async def query(cls, query_text):
        async with ConfigurationBasedLookupClient() as lookup:
            datasets = await lookup.by_query(query_text)

        return [await cls.from_lookup(lookup_dict) for lookup_dict in datasets]

    @classmethod
    async def query_all(cls):
        """Query all datasets from lookup server."""
        async with ConfigurationBasedLookupClient() as lookup:
            datasets = await lookup.all()

        return [await cls.from_lookup(lookup_dict) for lookup_dict in datasets]

    def __str__(self):
        return self._dataset_info['uri']

    def __getattr__(self, name):
        return self._dataset_info[name]

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._dataset_info[name] = value

    def __getstate__(self):
        return self._dataset_info

    def __setstate__(self, state):
        self._dataset_info = state

    def reload(self, uri=None):
        """Load the dataset from a URI.

        :param uri: URI to a dtoolcore.DataSet
        """
        self._dataset_info = _info(_load_dataset(uri))

    async def copy(self, target_base_uri, resume=False, auto_resume=True, progressbar=None):
        """Copy a dataset."""
        await _copy_dataset(self.uri, target_base_uri, resume, auto_resume, progressbar)

    def freeze(self):
        _load_dataset(str(self)).freeze()
        # We need to reread dataset after freezing, since _data is currently
        # a dtoolcore.ProtoDataSet but should not become a dtoolcore.DataSet
        self.reload()

    def put_readme(self, text):
        self.readme_content = text
        return _load_dataset(str(self)).put_readme(text)

    async def get_readme(self):
        if 'readme_content' in self._dataset_info:
            return self._dataset_info['readme_content']
        async with ConfigurationBasedLookupClient() as lookup:
            readme_dict = await lookup.readme(self.uri)
        self._dataset_info['readme_content'] = yaml.dump(readme_dict)
        return self._dataset_info['readme_content']

    async def get_manifest(self):
        if 'manifest' in self._dataset_info:
            return self._dataset_info['manifest']
        async with ConfigurationBasedLookupClient() as lookup:
            manifest_dict = await lookup.manifest(self.uri)
        self._dataset_info['manifest'] = _mangle_lookup_manifest(manifest_dict)
        return self._dataset_info['manifest']
