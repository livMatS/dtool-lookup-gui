dtool-gui
=========

dtool-gui is a graphical user interface for dtool_ and dtool-lookup-server_
written in Python_ and GTK_.

.. image:: data/screenshots/screenshot1.png

Installation
------------

The application uses setuptools_. It can be installed with pip_:

.. code:: bash

    pip install git+https://github.com/IMTEK-Simulation/dtool-gui.git

When checked out, either use pip_ or install via the standard route

.. code:: bash

   python setup.py install

Running the GUI
---------------

After installation, run the GUI with:

.. code:: bash

   python -m dtool_gui

Note that when you run the GUI for the first time, you will need to configure
the URL of the lookup and the authentication server as well as provide a
username and a password. To do this, click on the "Burger" symbol and select
*Settings*.

.. _dtool: https://github.com/jic-dtool/dtool

.. _dtool-lookup-server: https://github.com/jic-dtool/dtool-lookup-server

.. _Python: https://www.python.org/

.. _GTK: https://www.gtk.org/

.. _pip: https://pip.pypa.io/en/stable/

.. _setuptools: https://setuptools.readthedocs.io/en/latest/


Installation on MacOS
---------------------

The pip package for PyGObject has another name for macos. So comment it out in setup.py, install it following the instructions_ and then run `pip install /path/to/dtool-gui` 


.. _instructions: https://pygobject.readthedocs.io/en/latest/getting_started.html 

