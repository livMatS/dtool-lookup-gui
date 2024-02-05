#
# Copyright 2022-2023 Johannes Laurin Hörmann
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
import json
import logging
import pytest

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, GdkPixbuf

import gbulb
gbulb.install(gtk=True)

from dtool_lookup_gui.main import Application


logger = logging.getLogger(__name__)


_HERE = os.path.dirname(os.path.abspath(__file__))

# dtool_lookup_api Config

DTOOL_LOOKUP_SERVER_URL = "https://localhost:5000/lookup"
DTOOL_LOOKUP_SERVER_TOKEN = r"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwMTY4OTU5MywianRpIjoiYTdkN2Y5ZWItZGI3MS00YjExLWFhMzktZGQ2YzgzOTJmOWE4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InRlc3R1c2VyIiwibmJmIjoxNzAxNjg5NTkzLCJleHAiOjE3MDE2OTMxOTN9.t9SQ00ecZRc-pspz-Du7321xfWIzgTTFKobkNed1CuQYHvtNrc3vdHYbqCWaYCqZpEVF8RlltldT4Lookx6vNgnW4olpiS2KTZ-X2asMhn7SShDtUJuU54CGeViWzYX_V_Pzckoe_cgjFkOutRvnwy_072Whnmc0TwYojwNqUScAIJRu0pzym84JngloXfdI7r25GcRVNtzsGUl7DDfrIz4aSOeVDAVEXhPjgEatKsvNdVZl1DIJsTZpuI7Jh7ZW1WsyjonqHR0J0kIVQn9imQyLyS9_CtmURBQ3kabx6cxhpx5LADrzLutSu24eA4FyECOdzjJ3SPGb9nIVTEDxQg"
DTOOL_LOOKUP_SERVER_TOKEN_GENERATOR_URL = "https://localhost:5000/token"
DTOOL_LOOKUP_SERVER_USERNAME = "testuser"
DTOOL_LOOKUP_SERVER_PASSWORD = "test_password"
DTOOL_LOOKUP_SERVER_VERIFY_SSL = True

AFFIRMATIVE_EXPRESSIONS = ['true', '1', 'y', 'yes', 'on']
NEGATIVE_EXPRESSIONS = ['false', '0', 'n', 'no', 'off']

logger = logging.getLogger(__name__)

class MockDtoolLookupAPIConfig():
    """Mock dtool configuration without touching the local config file."""

    def __init__(self, *args, **kwargs):
        self._lookup_server_url = DTOOL_LOOKUP_SERVER_URL
        self._lookup_server_token = DTOOL_LOOKUP_SERVER_URL
        self._lookup_server_token_generator_url = DTOOL_LOOKUP_SERVER_TOKEN_GENERATOR_URL
        self._lookup_server_username = DTOOL_LOOKUP_SERVER_USERNAME
        self._lookup_server_password = DTOOL_LOOKUP_SERVER_PASSWORD
        self._lookup_server_verify_ssl = DTOOL_LOOKUP_SERVER_VERIFY_SSL


    @property
    def lookup_url(self):
        return self._lookup_server_url

    @lookup_url.setter
    def lookup_url(self, value):
        self._lookup_server_url = value

    # optional
    @property
    def token(self):
        return self._lookup_server_token

    @token.setter
    def token(self, token):
        self._lookup_server_token = token

    @property
    def auth_url(self):
        return self._lookup_server_token_generator_url

    @auth_url.setter
    def auth_url(self, value):
        self._lookup_server_token_generator_url = value

    @property
    def username(self):
        return self._lookup_server_username

    @username.setter
    def username(self, value):
        self._lookup_server_username = value

    @property
    def password(self):
        return self._lookup_server_password

    @password.setter
    def password(self, value):
        self._lookup_server_password = value

    @property
    def verify_ssl(self):
        return self._lookup_server_verify_ssl

    @verify_ssl.setter
    def verify_ssl(self, value):
        self._lookup_server_verify_ssl = value

# Config = DtoolLookupAPIConfig()


# ==========================================================================
# fixtures from https://github.com/beeware/gbulb/blob/main/tests/conftest.py
# ==========================================================================

def fail_test(loop, context):  # pragma: no cover
    loop.test_failure = context


def setup_test_loop(loop):
    loop.set_exception_handler(fail_test)
    loop.test_failure = None


def check_loop_failures(loop):  # pragma: no cover
    if loop.test_failure is not None:
        if hasattr(loop.test_failure, 'message') and hasattr(loop.test_failure, 'exception'):
            pytest.fail("{message}: {exception}".format(**loop.test_failure))
        else:
            pytest.fail("{message}".format(**loop.test_failure))


@pytest.fixture(scope="function")
def glib_policy():
    from gbulb.glib_events import GLibEventLoopPolicy

    logger.debug("Apply GLibEventLoopPolicy")
    return GLibEventLoopPolicy()


@pytest.fixture(scope="function")
def gtk_policy():
    from gbulb.gtk import GtkEventLoopPolicy
    logger.debug("Apply GtkEventLoopPolicy")
    return GtkEventLoopPolicy()


@pytest.fixture(scope="function")
def glib_loop(glib_policy):
    loop = glib_policy.new_event_loop()
    setup_test_loop(loop)
    logger.debug("Create GLibEventLoopPolicy event loop")

    yield loop

    check_loop_failures(loop)
    loop.close()


@pytest.fixture(scope="function")
def gtk_loop(gtk_policy):
    GObject.type_register(GtkSource.View)

    loop = gtk_policy.new_event_loop()
    # loop.set_application(Application(loop=loop))
    setup_test_loop(loop)
    logger.debug("Create GtkEventLoopPolicy event loop")

    yield loop

    check_loop_failures(loop)
    loop.close()


@pytest.fixture(scope="function")
def app(gtk_loop):
    app = Application(loop=gtk_loop)
    yield app

@pytest.fixture(scope="function")
def mock_token(scope="function"):
    """Provide a mock authentication token"""
    yield "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwMTY4OTU5MywianRpIjoiYTdkN2Y5ZWItZGI3MS00YjExLWFhMzktZGQ2YzgzOTJmOWE4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InRlc3R1c2VyIiwibmJmIjoxNzAxNjg5NTkzLCJleHAiOjE3MDE2OTMxOTN9.t9SQ00ecZRc-pspz-Du7321xfWIzgTTFKobkNed1CuQYHvtNrc3vdHYbqCWaYCqZpEVF8RlltldT4Lookx6vNgnW4olpiS2KTZ-X2asMhn7SShDtUJuU54CGeViWzYX_V_Pzckoe_cgjFkOutRvnwy_072Whnmc0TwYojwNqUScAIJRu0pzym84JngloXfdI7r25GcRVNtzsGUl7DDfrIz4aSOeVDAVEXhPjgEatKsvNdVZl1DIJsTZpuI7Jh7ZW1WsyjonqHR0J0kIVQn9imQyLyS9_CtmURBQ3kabx6cxhpx5LADrzLutSu24eA4FyECOdzjJ3SPGb9nIVTEDxQg"


@pytest.fixture(scope="function")
def mock_dataset_list():
    """Provide a mock dataset list"""
    with open(os.path.join(_HERE, 'data', 'mock_dataset_search_response.json'), 'r') as f:
        dataset_list = json.load(f)

    yield dataset_list


@pytest.fixture(scope="function")
def mock_manifest():
    """Provide a mock dataset list"""
    with open(os.path.join(_HERE, 'data', 'mock_manifest_response.json'), 'r') as f:
        manifest = json.load(f)

    yield manifest


@pytest.fixture(scope="function")
def mock_readme():
    """Provide a mock dataset list"""
    with open(os.path.join(_HERE, 'data', 'mock_readme_response.json'), 'r') as f:
        readme = json.load(f)

    yield readme


@pytest.fixture(scope="function")
def mock_config_info():
    """Provide a mock server config info"""
    with open(os.path.join(_HERE, 'data', 'mock_config_info_response.json'), 'r') as f:
        config_info = json.load(f)

    yield config_info


@pytest.fixture(scope="function")
def local_dataset_uri(tmp_path):
    """Create a proper local dataset to test against."""

    from dtoolcore import ProtoDataSet, generate_admin_metadata
    from dtoolcore.storagebroker import DiskStorageBroker

    name = "test_dataset"
    admin_metadata = generate_admin_metadata(name)
    dest_uri = DiskStorageBroker.generate_uri(
        name=name,
        uuid=admin_metadata["uuid"],
        base_uri=str(tmp_path))

    # create a proto dataset
    proto_dataset = ProtoDataSet(
        uri=dest_uri,
        admin_metadata=admin_metadata,
        config_path=None)
    proto_dataset.create()
    proto_dataset.put_readme("")

    # put two local files
    handle = "sample_dataset_content.txt"
    local_file_path = os.path.join(_HERE, 'data', handle)
    proto_dataset.put_item(local_file_path, handle)

    second_fname = "tiny.png"
    local_file_path = os.path.join(_HERE, 'data', second_fname)
    proto_dataset.put_item(local_file_path, second_fname)

    proto_dataset.freeze()

    yield dest_uri

@pytest.fixture(scope="function")
def populated_app_with_mock_data(
        app, mock_dataset_list, mock_manifest, mock_readme, mock_config_info):
    """Replaces lookup api calls with mock methods that return fake lists of datasets."""

    import dtool_lookup_api.core.config
    dtool_lookup_api.core.config.Config = MockDtoolLookupAPIConfig()

    # TODO: figure out whether mocked methods work as they should
    with (
            patch("dtool_lookup_api.core.LookupClient.authenticate", return_value=mock_token),
            patch("dtool_lookup_api.core.LookupClient.ConfigurationBasedLookupClient.connect", return_value=None),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.all", return_value=mock_dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.search", return_value=mock_dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.graph", return_value=[]),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.manifest", return_value=mock_manifest),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.readme", return_value=mock_readme),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.config", return_value=mock_config_info),
            patch("dtool_lookup_api.core.LookupClient.ConfigurationBasedLookupClient.has_valid_token", return_value=True)
        ):

        yield app


@pytest.fixture(scope="function")
def populated_app_with_local_dataset_data(
        app, local_dataset_uri, mock_token, mock_readme, mock_config_info):
    """Replaces lookup api calls with mock methods that return fake lists of datasets."""

    import dtool_lookup_api.core.config
    dtool_lookup_api.core.config.Config = MockDtoolLookupAPIConfig()

    from dtoolcore import DataSet
    dataset = DataSet.from_uri(local_dataset_uri)

    dataset_info = dataset._admin_metadata
    # this returns a dict like
    #   {'uuid': 'f9904c40-aff3-43eb-b062-58919c00062a',
    #    'dtoolcore_version': '3.18.2',
    #    'name': 'test_dataset',
    #    'type': 'dataset',
    #    'creator_username': 'jotelha',
    #    'created_at': 1702902057.239987,
    #    'frozen_at': 1702902057.241831
    #   }


    dataset_info["uri"] = dataset.uri
    dataset_info["base_uri"] = os.path.dirname(local_dataset_uri)

    dataset_list = [dataset_info]

    manifest = dataset.generate_manifest()

    with (
            patch("dtool_lookup_api.core.LookupClient.authenticate", return_value=mock_token),
            patch("dtool_lookup_api.core.LookupClient.ConfigurationBasedLookupClient.connect", return_value=None),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.all", return_value=dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.search", return_value=dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.graph", return_value=[]),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.manifest", return_value=manifest),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.readme", return_value=mock_readme),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.config", return_value=mock_config_info),
            patch("dtool_lookup_api.core.LookupClient.ConfigurationBasedLookupClient.has_valid_token", return_value=True)
        ):

        yield app


# ================================================================
# fixtures related to https://github.com/pytest-dev/pytest-asyncio
# ================================================================

# override https://github.com/pytest-dev/pytest-asyncio default event loop
@pytest.fixture(scope="function")
def event_loop(gtk_loop, app):
    gtk_loop.set_application(app)
    yield gtk_loop