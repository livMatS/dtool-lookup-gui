dtool-lookup-gui
================

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

