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

from io import StringIO

from ruamel.yaml import YAML

from dtoolcore import generate_admin_metadata, generate_proto_dataset
from dtoolcore.utils import get_config_value, write_config_value_to_file, _get_config_dict_from_file, \
    generous_parse_uri, name_is_valid, NAME_VALID_CHARS_LIST
from dtool_create.dataset import _get_readme_template
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient

from .datasets import DatasetModel
from .settings import settings


class BaseURI:
    """Model for all base URIs"""

    def __init__(self, uri_name):
        self._uri_name = uri_name
        self._cache = None

    def __str__(self):
        return f'{self._scheme}://{self._uri_name}'

    def __eq__(self, other):
        return self.scheme == other.scheme and self.uri_name == other.uri_name

    async def all_datasets(self):
        if self._cache is None or not self._use_cache:
            self._cache = await DatasetModel.all(str(self))
        return self._cache

    @classmethod
    @property
    def scheme(cls):
        return cls._scheme

    @property
    def uri_name(self):
        return self._uri_name


class LocalBaseURIModel(BaseURI):
    """Model for directory on local system"""

    _scheme = 'file'
    _use_cache = False

    _local_base_uris = settings.local_base_uris

    @classmethod
    def add_directory(cls, path):
        base_uri = generous_parse_uri(path)
        if base_uri.scheme != cls._scheme:
            raise ValueError(f"The URI provided specified schema '{base_uri.scheme}', but this base URI model "
                             f"supports '{cls._scheme}'.")
        cls._local_base_uris += [base_uri.path]
        # Store such that they will reappear when restarting the program
        settings.local_base_uris = cls._local_base_uris

    @classmethod
    def remove(cls, base_uri):
        i = cls._local_base_uris.index(base_uri.uri_name)
        if i >= 0:
            del cls._local_base_uris[i]
            # Store such that they will be removed when restarting the program
            settings.local_base_uris = cls._local_base_uris

    @classmethod
    def all(cls):
        return [cls(base_uri) for base_uri in cls._local_base_uris]

    def create_dataset(self, name, readme_template_path=None):
        """Create a proto dataset."""
        # Adopted from https://github.com/jic-dtool/dtool-create/blob/master/dtool_create/dataset.py#L133

        # Check that the name is valid
        if not name_is_valid(name):
            valid_chars = " ".join(NAME_VALID_CHARS_LIST)
            raise ValueError(f"Invalid dataset name '{name}'. "
                             f"Name must be 80 characters or less. "
                             f"Dataset names may only contain the characters: {valid_chars}")

        # Administrative metadata (dtool version, etc.)
        admin_metadata = generate_admin_metadata(name)

        # Create the dataset
        proto_dataset = generate_proto_dataset(
            admin_metadata=admin_metadata,
            base_uri=f'{self.scheme}:{self.uri_name}')
        proto_dataset.create()  # May raise StorageBrokerOSError

        # Initialize with template README.yml
        try:
            readme_template = _get_readme_template(readme_template_path)
        except FileNotFoundError:
            # FIXME: Show an error that template could not be found
            readme_template = ''
        yaml = YAML()
        yaml.explicit_start = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        descriptive_metadata = yaml.load(readme_template)
        stream = StringIO()
        yaml.dump(descriptive_metadata, stream)
        proto_dataset.put_readme(stream.getvalue())

        # Wrap in dataset model
        return DatasetModel.from_dataset(proto_dataset)


class ConfigBaseURIModel(BaseURI):
    """Model for dtool config-file based base URIs"""

    _use_cache = True

    @classmethod
    def all(cls):
        base_uris = []
        for key, value in _get_config_dict_from_file().items():
            if key.startswith(cls._prefix):
                base_uris += [cls(key[len(cls._prefix):])]
        return base_uris

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattr__(name)
        try:
            return get_config_value(self._properties[name].format(self._name), default='')
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'" )

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super().__setattr__(name, value)
        try:
            return write_config_value_to_file(self._properties[name].format(self._name), value)
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'" )


class S3BaseURIModel(ConfigBaseURIModel):
    """Model for managing S3 base URIs."""

    _scheme = 's3'
    _prefix = 'DTOOL_S3_ENDPOINT_'
    _properties = {
        'endpoint': 'DTOOL_S3_ENDPOINT_{}',
        'access_key_id': 'DTOOL_S3_ACCESS_KEY_ID_{}',
        'secret_access_key': 'DTOOL_S3_SECRET_ACCESS_KEY_{}',
        'dataset_prefix': 'DTOOL_S3_DATASET_PREFIX',
    }


class SMBBaseURIModel(ConfigBaseURIModel):
    """Model for managing SMB base URIs."""

    _scheme = 'smb'
    _prefix = 'DTOOL_SMB_SERVER_NAME_'
    _properties = {
        'server_name': 'DTOOL_SMB_SERVER_NAME_{}',
        'server_port': 'DTOOL_SMB_SERVER_PORT_{}',
        'domain': 'DTOOL_SMB_DOMAIN_{}',
        'service_name': 'DTOOL_SMB_SERVICE_NAME_{}',
        'path': 'DTOOL_SMB_PATH_{}',
        'username': 'DTOOL_SMB_USERNAME_{}',
        'password': 'DTOOL_SMB_PASSWORD_{}',
    }


class LookupBaseURIModel(BaseURI):
    """Model for base URIs obtained from lookup server"""

    @classmethod
    async def all(cls, username):
        async with ConfigurationBasedLookupClient() as lookup_client:
            user_info = await lookup_client.user_info(username)
        if 'search_permissions_on_base_uris' not in user_info:
            raise RuntimeError(f"Request for user '{username}' info failed, possibly not authenticated.")

        base_uris = user_info['search_permissions_on_base_uris']

        return [cls(base_uri) for base_uri in base_uris]

    def __init__(self, base_uri):
        p = generous_parse_uri(base_uri)
        self._scheme = p.scheme
        self._uri_name = p.netloc


_base_uri_models = [S3BaseURIModel, SMBBaseURIModel]


async def all(local=True, lookup=None):
    """
    Discover base URIs, either local or remote.

    Parameters
    ----------
    local : bool, optional
        List local base URIs. (Default: true)
    lookup : str, optional
        Query lookup server for additional base URIs registered with the
        lookup server but not registered locally. The `lookup` parameter
        receives the username used for authentication. (Default: None)

    Returns
    -------
    base_uris : list of :obj:`BaseURI`
        List of all discovered base URIs
    """
    base_uris = []
    for model in _base_uri_models:
        base_uris += model.all()
    if local:
        base_uris += LocalBaseURIModel.all()
    if lookup is not None:
        for base_uri in await LookupBaseURIModel.all(lookup):
            if not base_uri in base_uris:
                base_uris += [base_uri]
    return base_uris
