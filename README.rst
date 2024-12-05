dtool-lookup-gui
================

.. image:: data/icons/22x22/dtool_logo.png
    :height: 20px
    :target: https://github.com/livMatS/dtool-lookup-gui
    :alt: dtool-lookup-gui icon
.. image:: https://img.shields.io/github/actions/workflow/status/livMatS/dtool-lookup-gui/build-and-publish.yml?branch=master
    :target: https://github.com/livMatS/dtool-lookup-gui/actions/workflows/build-and-publish.yml
    :alt: GitHub Build Workflow Status
.. image:: https://img.shields.io/github/actions/workflow/status/livMatS/dtool-lookup-gui/test.yml?branch=master&label=tests
    :alt: GitHub Tests Workflow Status
    :target: https://github.com/livMatS/dtool-lookup-gui/actions/workflows/test.yml
.. image:: https://img.shields.io/github/v/release/livMatS/dtool-lookup-gui
    :target: https://github.com/livMatS/dtool-lookup-gui/releases/latest
    :alt: GitHub release (latest by date)
.. image:: https://badge.fury.io/py/dtool-lookup-gui.svg
    :target: https://badge.fury.io/py/dtool-lookup-gui
    :alt: PyPI package

dtool-lookup-gui is a graphical user interface for dtool_, the dtool-lookup-server_, the dtool-lookup-server-direct-mongo-plugin_ and the
dtool-lookup-server-dependency-graph-plugin_ written in Python_ and GTK_.

.. image:: data/screenshots/screenshot1.png

Quick start
-----------

Just download the pre-packaged binaries of the `latest release`_.

If the binaries won't run out-of-the-box on your system, continue below.

OS-specific notes
-----------------

Windows
^^^^^^^

The Windows executable comes in two variants, as a single portable file and an installer.

macOS
^^^^^

The app bundle requires MacOS 14.7 at least.
After downloading the `dmg` Apple Disk Image of the `latest release`_
and copying `dtool-lookup-gui` over to your `Applications` folder,
*macOS* will likely complain about `dtool-lookup-gui` being damaged
and refuse to execute it. This is due to the fact that we are no
Apple-verified developers. To run the app anyway, open a terminal and
remove Apple's quarantine attribute from the app with

.. code:: bash

    sudo xattr -rds com.apple.quarantine /Applications/dtool-lookup-gui.app

That should enable you to launch the app as usual. Another option is to
call

.. code:: bash

    /Applications/dtool-lookup-gui.app/Contents/MacOS/dtool-lookup-gui

directly from the command line.

Linux
^^^^^

After downloading and extracting the tar.gz-packaged Linux build, you may
run the bundled scripts :code:`set_launcher_icon.sh` and :code:`soft_link_launcher.sh`
subsequently to add this launcher icon to your desktop environment:

.. image:: data/screenshots/screenshot-ubuntu-launcher.png

This has been tested on Ubuntu 20.04 and GNOME 3.36.8.

The packaged Linux build will fail to launch out-of-the box under Wayland. 
An error like this might arise:

.. code::

   GLib-GIO-ERROR **: 11:26:50.444: Settings schema 'org.gnome.settings-daemon.plugins.xsettings' does not contain a key named 'antialiasing'
   Trace/breakpoint trap (core dumped)

If unsure which display server is in use, check with

.. code:: bash

   echo $XDG_SESSION_TYPE
   
This will likely output either :code:`x11` or :code:`wayland`.
If you are using Wayland, launch the app with environment variable 
:code:`GDK_BACKEND=x11` set, e.g. via

.. code:: bash

    GDK_BACKEND=x11 ./dtool_lookup_gui


Use
---

Searching
^^^^^^^^^

The app searches the index of a dtool-lookup-server. How exactly the index is searched depends on the implementation of the search plugin on the server side.
In the case of the reference search plugin, the `dtool-lookup-server-search-plugin-mongo`_, a word in the search field will search for exactly that word within all string fields stored in the underlying database.
This, of course, includes the content of the `README.yml` file attached to a dataset, but also matches against contents of the manifest (such as file names of the packaged items) and the basic set of  administrative metadata, namely the fields

.. code:: json

    {
        "base_uri": "s3://test-bucket",
        "created_at": 1683797360.056,
        "creator_username": "jotelha",
        "dtoolcore_version": "3.18.2",
        "frozen_at": 1683797362.855,
        "name": "test_dataset_2",
        "number_of_items": 1,
        "size_in_bytes": 19347,
        "tags": [],
        "type": "dataset",
        "uri": "s3://test-bucket/26785c2a-e8f8-46bf-82a1-cec92dbdf28f",
        "uuid": "26785c2a-e8f8-46bf-82a1-cec92dbdf28f"
    }

The `dtool-lookup-server-search-plugin-mongo`_ README offers more information on the exact search mechanism.

If the `dtool-lookup-server-direct-mongo-plugin`_ is installed on the server side, very specific search queries that make use of operators from the MongoDB language are possible.
Enclose a MongoDB language query in curly brackets ``{...}`` and all fields in double quotes ``"..."`` to use this direct Mongo query functionality.

The query

.. code:: json

    {
       "creator_username": {
            "$in": ["anna", "bert"]
        },
        "readme.description": {
            "$regex": "toluene"
        }
    }

searches for all datasets created by users with the either the local user name "anna" or "bert" on the machine of dataset creation and with the word "toluene" included in the README field "description".
The regular expression operator can of course formulate more sophisticated criteria than a plain text search on the content of a specific field.

The `direct query`_ section of the `dtool-lookup-server-direct-mongo-plugin`_ README lists a few
other query examples.

Development
-----------

Please read the `contributing guidelines`_ before diving into the development process.

Requirements
^^^^^^^^^^^^

This application requires Gtk_ 3 and GtkSourceView_ 4.

On Ubuntu (20.04),

.. code:: bash

    apt install -y gir1.2-gtksource-4

suffices to to install these dependencies from the standard system package repositories.

On recent macOS (>= 10.15) use homebrew, 

.. code:: bash

   brew install gtksourceview4 gnome-icon-theme

On earlie macOs, `MacPorts <https://www.macports.org/>`_ allows the installation of `gtksourceview4`

.. code:: bash
   
   sudo port -v selfupdate
   sudo port install xorg-server
   sudo port install gtksourceview4 py-gobject3 py-pip py-numpy py-scipy
   sudo port install adwaita-icon-theme

   sudo port select --set python python310
   sudo port select --set pip pip310

   mkdir -p ~/venv
   python -m venv --system-site-packages ~/venv/python-3.10
   source ~/venv/python-3.10/bin/activate
   
   pip install --upgrade pip
   pip install wheel
   pip install dtool-lookup-gui dtool-s3 dtool-smb


This has been tested on macOS 10.13.6.

On Windows, use `mingw64/msys2 <https://www.msys2.org>`_ and refer to the
`Using GTK from MSYS2 packages <https://www.gtk.org/docs/installations/windows#using-gtk-from-msys2-packages>`_
on the GTK project's pages.

Also refer to the build workflows `.github/workflows/build-on-[linux|macos|windows].yml` within this repository 
for understanding the requirements for the different systems.

On Windows WSL, install

    apt install gcc cmake python3-dev libcairo2-dev gir1.2-gtksource-4 libgirepository1.0-dev

to allow a development installation of the GUI as described below.

Installation
^^^^^^^^^^^^

For a locally editable install, clone this repository with

.. code:: console

    git clone git+https://github.com/livMatS/dtool-lookup-gui.git

change into the repository directory,

.. code:: bash

    cd dtool-lookup-gui

create and activate a clean virtual environment,

.. code:: bash

    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip

and perform an editable install with

.. code:: bash

   pip install -e .

Also run

.. code:: bash

   glib-compile-schemas .

from within subdirectory ``dtool_lookup_gui``. Otherwise, GUI launch fails with

.. code::

   gi.repository.GLib.Error: g-file-error-quark: Failed to open file “/path/to/repository/dtool_lookup_gui/gschemas.compiled”: open() failed: No such file or directory (4)


Running the GUI
---------------

After installation, run the GUI with:

.. code:: bash

   python -m dtool_lookup_gui

Note that when you run the GUI for the first time, you will need to configure
the URL of the lookup and the authentication server as well as provide a
username and a password. To do this, click on the "Burger" symbol and select
*Settings*.


Pinned requirements
^^^^^^^^^^^^^^^^^^^

``requirements.in`` contains unpinned dependencies. ``requirements.txt`` with pinned versions has been auto-generated with

.. code:: bash

  pip install pip-tools
  pip-compile --resolver=backtracking requirements.in > requirements.txt

GTK debugging
^^^^^^^^^^^^^

After

.. code-block:: bash

  gsettings set org.gtk.Settings.Debug enable-inspector-keybinding true

use CTRL-SHIFT-D during execution to display the GTK inspector for interactive debugging.

GUI design
^^^^^^^^^^

The GUI uses custom Gtk widgets. To edit the the XML UI definition files with
Glade_, add the directory ``glade/catalog`` to `Extra Catalog & Template paths`
within Glade's preferences dialog.

Running unit tests
^^^^^^^^^^^^^^^^^^

Running the unit tests requires `pytest` and `pytest-asyncio`. Then, run all tests from repository root with `pytest`.

Funding
-------

This development has received funding from the Deutsche Forschungsgemeinschaft within the Cluster of Excellence livMatS_.

.. _contributing guidelines: CONTRIBUTING.md

.. _direct query: https://github.com/livMatS/dtool-lookup-server-direct-mongo-plugin#direct-query

.. _dtool: https://github.com/jic-dtool/dtool

.. _dtool-lookup-server: https://github.com/jic-dtool/dtool-lookup-server

.. _dtool-lookup-server-dependency-graph-plugin: https://github.com/livMatS/dtool-lookup-server-dependency-graph-plugin

.. _dtool-lookup-server-direct-mongo-plugin: https://github.com/livMatS/dtool-lookup-server-direct-mongo-plugin

.. _dtool-lookup-server-search-plugin-mongo: https://github.com/jic-dtool/dtool-lookup-server-search-plugin-mongo

.. _Glade: https://glade.gnome.org/

.. _GTK: https://www.gtk.org/

.. _GtkSourceView: https://wiki.gnome.org/Projects/GtkSourceView

.. _pip: https://pip.pypa.io/en/stable/

.. _Python: https://www.python.org/

.. _setuptools: https://setuptools.readthedocs.io/en/latest/

.. _livMatS: https://www.livmats.uni-freiburg.de/en

.. _latest release: https://github.com/livMatS/dtool-lookup-gui/releases/latest

