Change log for dtool-lookup-gui
===============================

Unreleased
----------

- Bump to dtool-s3==0.14.0, replaces DTOOL_S3_DATASET_PREFIX by bucket-specific DTOOL_S3_DATASET_PREFIX_<BUCKET NAME>

0.5.1 (03Mar22)
---------------

- Button 'Show' opens file system browser in frozen executables as well, even on Windows

0.5.0 (02Mar22)
---------------

- About dialog with version info
- Offer multi-line search query editor via drp-down button instead of double click
- Button 'Show' opens file system browser in frozen executables as well
- Display correct number of copied items
- Added missing gir1.2-gtksource-4 system package dependency to Ubuntu build workflow
- Preserve executable bits in release archives
- Don't fail listing proto datasets without README.yml via dtool-s3 (or any other storage broker)

0.4.5 (28Feb22)
---------------

- Added refresh button
- Handle non-ASCII characters in S3 metadata by using dtool-s3 development version

0.4.4 (21Feb22)
---------------

- Packaged binary for MacOS >= 10.15
- Build system description bundled with binaries
- Moved repository from https://github.com/IMTEK-Simulation/dtool-lookup-gui to https://github.com/livMatS/dtool-lookup-gui

0.4.3 (17Feb22)
---------------

- README.yml template file chooser in settings dialog
- User name and eMail configurable in settings dialog

0.4.2 (09Feb22)
----------------

- Config reset/import/export buttons in settings dialog

0.4.1 (04Feb22)
---------------

- Usable and stable on Windows 10 and Ubuntu 20.04
- Published as PyInstaller-bundled one-file exectuable on GitHub releases
- Download of single items by double-click on manifest entry

0.4.0 (16Dec21)
---------------

- Manage (create, edit, freeze, copy) datasets in local directories and on
  remote (cloud) storage systems
- Configure dtool cloud endpoints

0.3.0 (15May21)
---------------

- Download files from manifest

0.2.1 (26Oct20)
---------------

- Show missing datasets with triangles
- Bug: Missing datasets
- Bug: Symbols in graph view

0.2.0 (26Oct20)
---------------

- Warn about missing UUIDs
- Tree view for manifest (#2)

0.1.2 (24Oct20)
---------------

- Removed debug print

0.1.1 (24Oct20)
---------------

- Show server version in status bar

0.1.0 (8Oct20)
--------------

- GTK client for dtool-lookup-server
- List all datasets and full text search
- Show metadata (README.yml) and manifest
- Optional: MongoDB queries
- Optional: Depedency graph visualization 
