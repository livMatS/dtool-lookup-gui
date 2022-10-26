import asyncio
import logging
import pytest

from dtool_lookup_gui.views.main_window import MainWindow

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.mark.asyncio
async def test_app_main_window_is_active(app):
    # app.props: ['action_group',
    #  'active_window',
    #  'app_menu',
    #  'application_id',
    #  'flags',
    #  'inactivity_timeout',
    #  'is_busy',
    #  'is_registered',
    #  'is_remote',
    #  'menubar',
    #  'register_session',
    #  'resource_base_path',
    #  'screensaver_active']
    # the main window only becomes active after startup, needs a little time
    await asyncio.sleep(1)
    assert isinstance(app.props.active_window, MainWindow)


@pytest.mark.asyncio
async def test_app_list_actions(app):
    assert set(app.list_actions()) == set([
        'toggle-logging',
        'reset-config',
        'set-loglevel',
        'set-logfile',
        'export-config',
        'import-config'])
