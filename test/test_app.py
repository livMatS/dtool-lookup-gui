#
# Copyright 2022-2023 Johannes Laurin Hörmann
#           2023 Ashwin Vazhappilly
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
import pytest

from dtool_lookup_gui.views.about_dialog import AboutDialog
from dtool_lookup_gui.views.config_details import ConfigDialog
from dtool_lookup_gui.views.settings_dialog import SettingsDialog
from dtool_lookup_gui.views.log_window import LogWindow
from dtool_lookup_gui.views.login_window import LoginWindow
from dtool_lookup_gui.views.main_window import MainWindow
from dtool_lookup_gui.views.server_versions_dialog import ServerVersionsDialog
from dtool_lookup_gui.views.error_linting_dialog import LintingErrorsDialog

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
    assert set(window_types) == set([AboutDialog,
                                     ConfigDialog,
                                     SettingsDialog,
                                     ServerVersionsDialog,
                                     LogWindow,
                                     MainWindow,
                                     LintingErrorsDialog])


@pytest.mark.asyncio
async def test_app_list_actions(app):
    assert set(app.list_actions()) == set([
        'toggle-logging',
        'reset-config',
        'renew-token',
        'set-loglevel',
        'set-logfile',
        'export-config',
        'import-config'])
