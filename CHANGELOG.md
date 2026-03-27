Change log for dtool-lookup-gui
===============================

0.7.3 (unreleased)
-------------------

- CI: fix test workflow — add missing `glib-compile-schemas` step that was
  causing all test jobs to fail since early 2026 (GLib.Error on settings import)
- CI: update Python test matrix to 3.10–3.13 (drop EOL 3.9, add 3.13)
- BUG: fix `collect_number_of_tests.py` propagating error text to stdout,
  which caused `pytest -n "Error..."` to fail with invalid numprocesses value
- MAINT: fix typo in `build-on-ubuntu` workflow name
- BUG: fix defunct Linux bundle — explicitly bundle GI typelibs (Gtk-3.0,
  GLib-2.0, Gio-2.0, Pango-1.0, GtkSource-4, GdkPixbuf-2.0, etc.) in
  PyInstaller spec and set `GI_TYPELIB_PATH` in runtime hook so the bundled
  app can find them; previously all GI modules were silently missing
- CI: fix Ubuntu build workflow — run PyInstaller under xvfb-run so GI hook
  child processes can initialise GTK; add smoke-test step that verifies
  the bundle starts without crashing before uploading artifacts
- BUG: fix Linux bundle missing `GObject.type_register` and other `gi.overrides`
  Python wrappers; PyInstaller's GI hook skips overrides when module introspection
  fails; explicitly collect all `gi.overrides` submodules as hidden imports
- BUG: fix `dtool_lookup_gui/utils/about.py` using `pkg_resources.iter_entry_points`
  (unavailable in Python 3.12+); replace with `importlib.metadata` shim
- BUG: fix Linux bundle crashing with `ModuleNotFoundError: No module named
  'dtool_cli.cli'` — `dtool-cli 0.7.1` uses `pkg_resources.iter_entry_points`
  (removed from Python 3.12+) and calls `pretty_version_text()` eagerly at
  module import time, causing PyInstaller analysis to fail and silently exclude
  the module from the bundle; vendor a fixed `dtool_cli/cli.py` in
  `pyinstaller/vendored/` (importlib.metadata shim + deferred version call)
  and overwrite the installed copy before PyInstaller runs via
  `pyinstaller/vendored/override_dtool_cli.py`

0.7.2 (13Nov25)
---------------

- Introduced switch for deactivating authentication against dserver
- Fixed save metadata button not working

0.7.1 (6Feb25)
---------------

- Introduced tree view of README.yml content
- Added `dtool-gui` script call
- Modified URL in about dialogue

0.7.0 (17Dec24)
---------------

- Login window
- Pagination for dserver lookup results
- Sorting for dserver lookup results
- Add/delete tags in GUI
- Add/delete annotations in GUI (key - value pairs)

0.6.2 (02Nov22)
---------------

- Item download settings (open after download, default download directory)
- New icons
- Fixed issue concerning duplicate local base URI entries

0.6.1 (07Apr22)
---------------

- Offer DMG image for macOS
- Bundle xpm icons with all distributions

0.6.0 (29Mar22)
---------------

- Handle errors in dataset copy child processes correctly
- Include dtool icons and according licenses
- Release macOS .app and Windows installer
- Desktop launcher 
- Preserve non-ASCII characters in README.yml content received from lookup server
- Bump to ``dtool-s3==0.14.1``, replaces ``DTOOL_S3_DATASET_PREFIX`` by bucket-specific ``DTOOL_S3_DATASET_PREFIX_<BUCKET NAME>``

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
