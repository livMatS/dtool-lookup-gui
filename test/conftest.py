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


# ================================================================
# fixtures related to https://github.com/pytest-dev/pytest-asyncio
# ================================================================

# override https://github.com/pytest-dev/pytest-asyncio default event loop
@pytest.fixture(scope="function")
def event_loop(gtk_loop, app):
    gtk_loop.set_application(app)
    yield gtk_loop