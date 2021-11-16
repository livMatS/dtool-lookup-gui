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
import os
import logging

import dtoolcore

import dtool_gui_tk.models

from dtool_gui_tk.models import (
    _ConfigFileVariableBaseModel,
    LocalBaseURIModel,
    # DataSetListModel,
    DataSetModel,
    ProtoDataSetModel,
    MetadataSchemaListModel,
    UnsupportedTypeError,
    metadata_model_from_dataset
)

from dtool_info.inventory import _dataset_info

logger = logging.getLogger(__name__)


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


class RemoteBaseURIModel(_ConfigFileVariableBaseModel):
    "Model for managing local base URI."

    KEY = "DTOOL_REMOTE_BASE_URI"

    def get_base_uri(self):
        """Return the base URI.

        :returns: base URI where datasets will be read from and written to
        """
        return self._get()

    def put_base_uri(self, base_uri):
        """Put/update the base URI.

        The value is updated in the config file.

        :param base_uri: base URI
        """
        value = dtoolcore.utils.sanitise_uri(base_uri)
        self._put(value)


class BaseURIModel():
    "Model for managing base URI."

    def __init__(self, base_uri=os.path.curdir):
        self.put_base_uri(base_uri)

    def get_base_uri(self):
        """Return the base URI.

        :returns: base URI where datasets will be read from and written to
        """
        return self._base_uri

    def put_base_uri(self, base_uri):
        """Put/update the base URI.

        :param base_uri: base URI
        """
        value = dtoolcore.utils.sanitise_uri(base_uri)
        self._base_uri = value


class DataSetModel(dtool_gui_tk.models.DataSetModel):
    "Model for both frozen and ProtoDataSet."
    def load_dataset(self, uri):
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

        self._metadata_model = metadata_model_from_dataset(self._dataset)

    def reload(self):
        uri = self.dataset.uri
        self.clear()
        self.load_dataset(uri)

    @property
    def is_frozen(self):
        return isinstance(self._dataset, dtoolcore.DataSet)

    @property
    def dataset(self):
        return self._dataset


class DataSetListModel(dtool_gui_tk.models.DataSetListModel):
    "Model for managing all (frozen and proto) datasets in a base URI."

    def reindex(self):
        """Index the base URI."""
        self._datasets = []
        self._datasets_info = []
        self._active_index = None
        self._all_tags = set()
        base_uri = self._base_uri_model.get_base_uri()
        if base_uri is None:
            return

        # iter through proto datasets
        for ds in dtoolcore.iter_proto_datasets_in_base_uri(base_uri):
            append_okay = True
            ds_tags = set(ds.list_tags())
            self._all_tags.update(ds_tags)
            if self.tag_filter is not None and self.tag_filter not in ds_tags:
                append_okay = False
            if append_okay:
                self._datasets.append(ds)

                self._datasets_info.append(_proto_dataset_info(ds))

        # iter through frozen datasets
        for ds in dtoolcore.iter_datasets_in_base_uri(base_uri):
            append_okay = True
            ds_tags = set(ds.list_tags())
            self._all_tags.update(ds_tags)
            if self.tag_filter is not None and self.tag_filter not in ds_tags:
                append_okay = False
            if append_okay:
                self._datasets.append(ds)
                self._datasets_info.append(_dataset_info(ds))

        # The initial active index is 0 if there are datasets in the model.
        if len(self._datasets) > 0:
            self._active_index = 0

        self._rebuild_mappings()

    def _rebuild_mappings(self):
        """Make datasets and indices in lit accessible via URI and UUID."""
        self._datasets_by_uuid = {}
        self._datasets_by_uri = {}
        self._index_by_uuid = {}
        self._index_by_uri = {}
        for i, ds in enumerate(self._datasets):
            if ds.uuid not in self._datasets_by_uuid:
                self._datasets_by_uuid[ds.uuid] = []
                self._index_by_uuid[ds.uuid] = []
            self._datasets_by_uuid[ds.uuid].append(ds)
            self._index_by_uuid[ds.uuid].append(i)

            self._datasets_by_uri[ds.uri] = ds
            self._index_by_uri[ds.uri] = i

    def sort(self, *args, **kwargs):
        """Sort the datasets by items properties."""
        super().sort(*args, **kwargs)
        self._rebuild_mappings()

    def get_index_by_uri(self, uri):
       return self._index_by_uri[uri]

    def set_active_index_by_uri(self, uri):
       index = self.get_index_by_uri(uri)
       self.set_active_index(index)
