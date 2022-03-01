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
