import asyncio

import pytest
from unittest.mock import Mock, patch, ANY
from gi.repository import Gtk
from dtool_lookup_gui.views.main_window import MainWindow


@pytest.mark.asyncio
async def test_app_id(app):
    assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'


@pytest.mark.asyncio
async def test_do_refresh_view(app):
    """Test the do_refresh_view method triggers the refresh method."""
    
    # Actually activate the untempered method with all side effects
    app.main_window.do_refresh_view(None, None)

    # Patch the main window's refresh method and make sure it's called when
    # action activated via the Gtk framework
    with patch.object(app.main_window, 'refresh', new_callable=Mock) as mock_refresh:
        app.main_window.activate_action('refresh-view')
        mock_refresh.assert_called_once()
