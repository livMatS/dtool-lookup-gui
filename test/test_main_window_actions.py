from unittest.mock import patch, MagicMock, create_autospec, Mock
import pytest
from gi.repository import Gio, GLib, Gtk, GtkSource, Gdk
from dtool_lookup_gui.views.main_window import MainWindow

@pytest.fixture
def mocked_gtk_app():
    """Create a mocked GTK application."""
    mock_app = create_autospec(Gtk.Application, instance=True)
    # Set up any specific properties or return values you need for the mock here
    return mock_app

@pytest.fixture
def main_window_instance(mocked_gtk_app):
    """Create an instance of MainWindow for testing with a mocked GTK application."""
    with patch('dtool_lookup_gui.views.main_window.MainWindow') as mock_main_window:
        instance = mock_main_window(application=mocked_gtk_app)
        yield instance

@pytest.mark.asyncio
async def test_main_window_creation(main_window_instance):
    """Simple test to check if MainWindow is created with the mocked GTK application."""
    assert main_window_instance is not None
    assert isinstance(main_window_instance.application, MagicMock), "The application should be a MagicMock."
    assert isinstance(main_window_instance.builder, MagicMock), "The builder should be a MagicMock."
    assert isinstance(main_window_instance.window, MagicMock), "The window should be a MagicMock."
    assert isinstance(main_window_instance.search_button, MagicMock), "The search_button should be a MagicMock."
    assert isinstance(main_window_instance.search_entry, MagicMock), "The search_entry should be a MagicMock."
    assert isinstance(main_window_instance.search_results_treeview, MagicMock), "The search_results_treeview should be a MagicMock."


@pytest.mark.asyncio
async def test_do_refresh_view(main_window_instance):
    """Test the do_refresh_view action."""

    # Mock the necessary method
    with patch.object(main_window_instance, 'refresh', new_callable=Mock) as mock_refresh:
        # Mock the action and value as needed, adjust based on your actual method signature
        action = MagicMock()
        value = MagicMock()  # Adjust this if your action requires a specific value

        # Perform the refresh view action
        main_window_instance.do_refresh_view(action, value)

        # Assert that the refresh method was called
        mock_refresh.assert_called_once()
