dtool-lookup-gui
================

.. image:: https://badge.fury.io/py/dtool-lookup-gui.svg
    :target: https://badge.fury.io/py/dtool-lookup-gui
    :alt: PyPI package

dtool-lookup-gui is a graphical user interface for dtool_, dtool-lookup-server_ and
dtool-lookup-server-dependency-graph-plugin_ written in Python_ and GTK_.

.. image:: data/screenshots/screenshot1.png

Installation
------------

The application uses setuptools_. It can be installed with pip_:

.. code:: bash

    pip install dtool-lookup-gui

If you want the latest development release, then use:

.. code:: bash

    pip install git+https://github.com/IMTEK-Simulation/dtool-lookup-gui.git

When already clone into a local directly via `git`, either use pip_ or install via the standard route

.. code:: bash

   python setup.py install

Running the GUI
---------------

After installation, run the GUI with:

.. code:: bash

   python -m dtool_lookup_gui

Note that when you run the GUI for the first time, you will need to configure
the URL of the lookup and the authentication server as well as provide a
username and a password. To do this, click on the "Burger" symbol and select
*Settings*.

.. _dtool: https://github.com/jic-dtool/dtool

.. _dtool-lookup-server: https://github.com/jic-dtool/dtool-lookup-server

.. _dtool-lookup-server-dependency-graph-plugin: https://github.com/IMTEK-Simulation/dtool-lookup-server-dependency-graph-plugin

.. _Python: https://www.python.org/

.. _GTK: https://www.gtk.org/

.. _pip: https://pip.pypa.io/en/stable/

.. _setuptools: https://setuptools.readthedocs.io/en/latest/


Installation on MacOS
---------------------

The pip package for PyGObject has another name for macos. So comment it out in setup.py, install it following the instructions_ and then run `pip install /path/to/dtool-gui` 

.. _instructions: https://pygobject.readthedocs.io/en/latest/getting_started.html 

You also need to install the gnome icons in order for them to be displayed properly: 

.. code:: bash

   brew install gnome-icon-theme

If you get the error

.. code:: bash

    ** (process:56111): WARNING **: 07:31:36.107: Failed to load shared library 'libpango-1.0.0.dylib' referenced by the typelib: dlopen(libpango-1.0.0.dylib, 9):      image not found
    Traceback (most recent call last):
  File "/usr/local/Cellar/python@3.9/3.9.2_2/Frameworks/Python.framework/Versions/3.9/lib/python3.9/runpy.py", line 197, in _run_module_as_main
    return _run_code(code, main_globals, None,
  File "/usr/local/Cellar/python@3.9/3.9.2_2/Frameworks/Python.framework/Versions/3.9/lib/python3.9/runpy.py", line 87, in _run_code
    exec(code, run_globals)
  File "/usr/local/lib/python3.9/site-packages/dtool_lookup_gui/__main__.py", line 26, in <module>
    from .MainApplication import run_gui
  File "/usr/local/lib/python3.9/site-packages/dtool_lookup_gui/MainApplication.py", line 41, in <module>
    from gi.repository import Gtk, Gio
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 664, in _load_unlocked
  File "<frozen importlib._bootstrap>", line 627, in _load_backward_compatible
  File "/usr/local/lib/python3.9/site-packages/gi/importer.py", line 144, in load_module
    importlib.import_module('gi.repository.' + dep.split("-")[0])
  File "/usr/local/Cellar/python@3.9/3.9.2_2/Frameworks/Python.framework/Versions/3.9/lib/python3.9/importlib/__init__.py", line 127, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 664, in _load_unlocked
  File "<frozen importlib._bootstrap>", line 627, in _load_backward_compatible
  File "/usr/local/lib/python3.9/site-packages/gi/importer.py", line 144, in load_module
    importlib.import_module('gi.repository.' + dep.split("-")[0])
  File "/usr/local/Cellar/python@3.9/3.9.2_2/Frameworks/Python.framework/Versions/3.9/lib/python3.9/importlib/__init__.py", line 127, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 664, in _load_unlocked
  File "<frozen importlib._bootstrap>", line 627, in _load_backward_compatible
  File "/usr/local/lib/python3.9/site-packages/gi/importer.py", line 145, in load_module
    dynamic_module = load_overrides(introspection_module)
  File "/usr/local/lib/python3.9/site-packages/gi/overrides/__init__.py", line 118, in load_overrides
    override_mod = importlib.import_module(override_package_name)
  File "/usr/local/Cellar/python@3.9/3.9.2_2/Frameworks/Python.framework/Versions/3.9/lib/python3.9/importlib/__init__.py", line 127, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "/usr/local/lib/python3.9/site-packages/gi/overrides/Pango.py", line 41, in <module>
    FontDescription = override(FontDescription)
  File "/usr/local/lib/python3.9/site-packages/gi/overrides/__init__.py", line 195, in override
    assert g_type != TYPE_NONE
    AssertionError


A possible fix is 

.. code:: bash

    DYLD_LIBRARY_PATH="/System/Library/Frameworks/OpenGL.framework/Versions/A/Libraries/:/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Versions/A/Resources/:/usr/local/lib" python3.9 -m dtool_lookup_gui
    
See https://gitlab.gnome.org/GNOME/pygobject/-/issues/417 
