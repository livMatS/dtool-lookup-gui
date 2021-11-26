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

from dtoolcore.utils import get_config_value, write_config_value_to_file, _get_config_dict_from_file

from .datasets import DatasetModel


class ConfigBaseURIModel:
    """Model for config-file based base URIs"""

    def __init__(self, uri_name):
        self._uri_name = uri_name

    @classmethod
    def all(cls):
        base_uris = []
        for key, value in _get_config_dict_from_file().items():
            if key.startswith(cls._prefix):
                base_uris += [cls(key[len(cls._prefix):])]
        return base_uris

    def __str__(self):
        return f'{self._schema}://{self._uri_name}'

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

    def all_datasets(self):
        return DatasetModel.all(str(self))

class S3BaseURIModel(ConfigBaseURIModel):
    """Model for managing S3 base URIs."""

    _schema = 's3'
    _prefix = 'DTOOL_S3_ENDPOINT_'
    _properties = {
        'endpoint': 'DTOOL_S3_ENDPOINT_{}',
        'access_key_id': 'DTOOL_S3_ACCESS_KEY_ID_{}',
        'secret_access_key': 'DTOOL_S3_SECRET_ACCESS_KEY_{}',
        'dataset_prefix': 'DTOOL_S3_DATASET_PREFIX',
    }


class SMBBaseURIModel(ConfigBaseURIModel):
    """Model for managing SMB base URIs."""

    _schema = 'smb'
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


_base_uri_models = [S3BaseURIModel, SMBBaseURIModel]


def all():
    base_uris = []
    for model in _base_uri_models:
        base_uris += model.all()
    return base_uris
