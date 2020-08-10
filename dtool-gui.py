import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class SignalHandler:
    def onDestroy(self, *args):
        print('onDestroy')
        Gtk.main_quit()

    def onButtonPressed(self, arg1, arg2):
        print('Hello World!', arg1, arg2)

builder = Gtk.Builder()
builder.add_from_file('dtool-gui.glade')
builder.connect_signals(SignalHandler())

win = builder.get_object('main-window')
win.show_all()

Gtk.main()
