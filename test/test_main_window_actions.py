from unittest.mock import patch, MagicMock, create_autospec, Mock
import pytest
from gi.repository import Gtk
from dtool_lookup_gui.views.main_window import MainWindow


@pytest.mark.asyncio
async def test_do_refresh_view(app):
    """Test the do_refresh_view method triggers the refresh method."""
    
    # Actually activate the untempered method with all side effects
    app.main_window.do_refresh_view(None, None)

    # We could check for any effects of the action here, e.g.
    # have Gtk widgets been  populated with teh right data?

    # Patch the main window's refresh method and make sure it's called when
    # action activated via the Gtk framework
    with patch.object(app.main_window, 'refresh', new_callable=Mock) as mock_refresh:
        app.main_window.activate_action('refresh-view')
        mock_refresh.assert_called_once()

        # We could replace the refresh mock with mocks of other calls
        # embedded deeper in the hierarchy and assert that the call
        # hierarchy is preserved as we expect it
