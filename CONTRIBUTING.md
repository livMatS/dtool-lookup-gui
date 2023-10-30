Contributing to dtool-lookup-gui
================================

Code style
----------
Always follow [PEP-8](https://www.python.org/dev/peps/pep-0008/) with the exception of line breaks.

Development branches
--------------------
New features should be developed always in its own branch. When creating your own branch,
please prefix that branch by the date of creation.
For example, if you begin working on implementing pagination on 6th April 2023, the branch could be called `2023-04-06-pagination`.

Commits
-------
Prepend you commits with a shortcut indicating the type of changes they contain:
* `BUG`: Bug fix
* `CI`: Changes to the CI configuration
* `DEP`: Update in 3rd-party dependencies
* `DOC`: Changes to documentation strings
* `ENH`: Enhancement (e.g. a new feature)
* `MAINT`: Maintenance (e.g. fixing a typo)
* `TST`: Changes to the unit test environment
* `WIP`: Work in progress

GTK-specific
------------

The dtool-lookup-gui uses [GTK 3](/https://docs.gtk.org/gtk3/) to provide a platform-independent graphical user interface (GUI). 
GTK originates at the [GNOME](https://wiki.gnome.org/) project.
At it's core sits [GLib](https://gitlab.gnome.org/GNOME/glib/), and on top of that lives the [GObject](https://docs.gtk.org/gobject/) library. 
Again higher live the [Gio](https://docs.gtk.org/gio/) and [Gdk](https://docs.gtk.org/gdk4/) libraries and on top of them all the GTK toolkit.
The dtool-lookup-gui interfaces all GLib, GObject, Gio, Gtk, and Gdk functionality with [PyGObject](https://pygobject.readthedocs.io/en/latest/). 
The [Python GTK+ 3 Tutorial](https://python-gtk-3-tutorial.readthedocs.io/en/latest/) helps with learning how to build GTK applications with Python. 

Signals and events, and the event loop
--------------------------------------

GTK applications run asynchronously in the [GLib](https://docs.gtk.org/glib/) main event loop. [gbulb](https://github.com/beeware/gbulb) provides an implementation of the [PEP 3156](https://peps.python.org/pep-3156/) interface to this GLib event loop for Python-native use of [asyncio](https://docs.python.org/3/library/asyncio.html). 
Within the dtool-lookup-gui's code, and importantly within `test/conftest.py` you will hence find `gbulb` bits that configure `asyncio` and `GTK` to share the same event loop.

Gio.Action 
----------

Next to signals and events, actions are an important concept. 
[Actions](https://docs.gtk.org/gio/iface.Action.html) implement functionality that is not necessarily bound to a specific element in the graphical representation. 
Wrapping as much behavior as possible into atomic actions helps to structure the code and let the application evolve in the spirit of a clean separation between model, view, and controlling logic ([MVC software design pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)). 
Furthermore, actions can be evoked by other means than user interaction via the GUI, such as via the command line or a keyboard shortcut.
They facilitate writing unit tests as well.

When implementing new features, think about how to break them down into atomic actions. 
In most cases, you will want to use the [Gio.SimpleAction](https://lazka.github.io/pgi-docs/Gio-2.0/interfaces/SimpleAction.html) interface.
You will find usage examples within the code, in the [GTK Python developer handbook: Working with GIO Actions](https://bharatkalluri.gitbook.io/gnome-developer-handbook/writing-apps-using-python/working-with-gio-gactions). 
Write actions as methods prefixed with `do_*`, e.g. `do_search` and attach them to the app itself or to the window they relate to.
Write at least one unit test for each action, e.g. `test_do_search` for the action `do_search`.