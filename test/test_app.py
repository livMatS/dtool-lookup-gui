import asyncio
import logging
import pytest

from dtool_lookup_gui.views.about_dialog import AboutDialog
from dtool_lookup_gui.views.settings_dialog import SettingsDialog
from dtool_lookup_gui.views.log_window import LogWindow
from dtool_lookup_gui.views.main_window import MainWindow

logger = logging.getLogger(__name__)

# Some application properties to test against:
#
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


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.mark.asyncio
async def test_app_window_types(app):
    window_types = [type(win) for win in app.get_windows()]
    assert set(window_types) == set([AboutDialog, SettingsDialog, LogWindow, MainWindow])


@pytest.mark.asyncio
async def test_app_list_actions(app):
    assert set(app.list_actions()) == set([
        'toggle-logging',
        'reset-config',
        'set-loglevel',
        'set-logfile',
        'export-config',
        'import-config'])
