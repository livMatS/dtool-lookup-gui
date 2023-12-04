import json
import logging
import os
import pytest

from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, GdkPixbuf

import asyncio
import gbulb
gbulb.install(gtk=True)

import dtool_lookup_api.core.LookupClient

from dtool_lookup_gui.main import Application
from dtool_lookup_gui.views.main_window import MainWindow


logger = logging.getLogger(__name__)


_HERE = os.path.dirname(os.path.abspath(__file__))
# _ROOT = os.path.join(_HERE, "..")

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
        pytest.fail("{message}: {exception}".format(**loop.test_failure))


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
def mock_config_info():
    """Provide a mock server config info"""
    with open(os.path.join(_HERE, 'data', 'mock_config_info_response.json'), 'r') as f:
        config_info = json.load(f)

    yield config_info


@pytest.fixture(scope="function")
def app_without_authentication(app, mock_token):
    """Removes authentication from app."""
    with patch("dtool_lookup_api.core.LookupClient.authenticate", return_value=mock_token):
        yield app


@pytest.fixture(scope="function")
def app_with_mock_dtool_lookup_api_calls(
        app_without_authentication, mock_dataset_list, mock_config_info):
    """Replaces lookup api calls with mock methods that return fake lists of datasets."""

    # TODO: figure out whether mocked methods work as they should
    with (
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.all", return_value=mock_dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.search", return_value=mock_dataset_list),
            patch("dtool_lookup_api.core.LookupClient.TokenBasedLookupClient.config", return_value=mock_config_info),
            patch("dtool_lookup_api.core.LookupClient.ConfigurationBasedLookupClient.has_valid_token", return_value=True)
        ):

        yield app_without_authentication


@pytest.fixture(scope="function")
def populated_app(app_with_mock_dtool_lookup_api_calls):
    """Provides app populated with mock datasets."""

    # TODO: figure out how to populate and refresh app with data here before app launched
    # app.main_window.activate_action('refresh-view')

    yield app_with_mock_dtool_lookup_api_calls


# ================================================================
# fixtures related to https://github.com/pytest-dev/pytest-asyncio
# ================================================================

# override https://github.com/pytest-dev/pytest-asyncio default event loop
@pytest.fixture(scope="function")
def event_loop(gtk_loop, app):
    gtk_loop.set_application(app)
    yield gtk_loop