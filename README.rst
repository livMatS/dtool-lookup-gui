dtool-gui
=========

dtool-gui is a GTK+ GUI application for dtool_ and dtool-lookup-server_.

.. image:: data/screenshots/screenshot1.png

Installation
------------

The application uses setuptools_. It can be installed via pip:

.. code:: bash

    pip install https://github.com/IMTEK-Simulation/dtool-gui.git

When checked out, simply install via the standard route

.. code:: bash

   python setup.py install

Running the GUI
---------------

After installation, run the GUI via:

.. code:: bash

   python -m dtool_gui

Note that when you run the GUI for the first time, you will need to configure
the URL of the lookup and the authentication server as well as provide a
username and a password. To do this, click on the "Burger" symbol and select
*Settings*.

.. _dtool: https://github.com/jic-dtool/dtool

.. _dtool-lookup-server: https://github.com/jic-dtool/dtool-lookup-server

.. _setuptools: https://setuptools.readthedocs.io/en/latest/