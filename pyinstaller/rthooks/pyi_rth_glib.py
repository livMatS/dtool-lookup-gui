#-----------------------------------------------------------------------------
# Copyright (c) 2015-2021, PyInstaller Development Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: Apache-2.0
#-----------------------------------------------------------------------------

import os
import sys


# enable Gio.AppInfo to find system default apps,
# i.e. for use with Gio.AppInfo.launch_default_for_uri
xdg_data_dirs_orig = os.environ.get("XDG_DATA_DIRS", None)
xdg_data_dirs_prepend = os.path.join(sys._MEIPASS, 'share')

if xdg_data_dirs_orig is not None:
    os.environ['XDG_DATA_DIRS_ORIG'] = xdg_data_dirs_orig
    os.environ['XDG_DATA_DIRS'] = xdg_data_dirs_prepend + os.pathsep + xdg_data_dirs_orig
else:
    os.environ['XDG_DATA_DIRS'] = xdg_data_dirs_prepend

# Set GI_TYPELIB_PATH so gi.repository can find the bundled typelib files.
# PyInstaller bundles typelibs into the gi_typelibs/ subdirectory of _MEIPASS.
# Without this, the bundled app raises:
#   gi.RepositoryError: Typelib file for namespace 'Gtk', version '3.0' not found
#
# We prepend the bundled path but also keep system paths as fallback so that
# any typelib not explicitly bundled is still found on the host system.
gi_typelib_path = os.path.join(sys._MEIPASS, 'gi_typelibs')
gi_typelib_path_orig = os.environ.get("GI_TYPELIB_PATH", None)

# Build the combined path: bundled first, then system fallbacks
system_typelib_dirs = [
    '/usr/lib/x86_64-linux-gnu/girepository-1.0',
    '/usr/lib/girepository-1.0',
    '/usr/lib64/girepository-1.0',
    '/usr/local/lib/girepository-1.0',
]
system_typelib_path = os.pathsep.join(d for d in system_typelib_dirs if os.path.isdir(d))

parts = [p for p in [gi_typelib_path, gi_typelib_path_orig, system_typelib_path] if p]
os.environ['GI_TYPELIB_PATH'] = os.pathsep.join(parts)
