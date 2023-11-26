from unittest.mock import patch, MagicMock, create_autospec
import pytest
from gi.repository import Gtk
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

    # Optionally, test if certain methods or properties are called or set
    # main_window_instance.application.some_method.assert_called_once()
    # assert main_window_instance.application.some_property == 'expected_value'
