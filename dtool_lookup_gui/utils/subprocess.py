#
# Copyright 2022 Johannes Laurin Hörmann
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import logging
import os
import platform
import subprocess

from dtoolcore.utils import generous_parse_uri

from ..utils.environ import TemporaryOSEnviron


from gi.repository import Gio


logger = logging.getLogger(__name__)


def launch_default_app_for_uri(uri):
    """Launch OS- and environment-dependent default application for URI."""
    parsed_uri = generous_parse_uri(uri)
    if parsed_uri.scheme != 'file':
        logger.warning("Only meant to open local resources. URI scheme '%s' not supported.", parsed_uri.scheme)

    filepath = parsed_uri.path
    logger.debug("URI '%s' corresponds to local path '%s'.", uri, filepath)

    # This workaround for launching external system applications from
    # within a frozen app as suggested on
    # https://pyinstaller.readthedocs.io/en/stable/runtime-information.html#ld-library-path-libpath-considerations
    # likely not be necessary here. It may, however, be necessary for
    # opening arbitrary file types.
    lp_key = 'LD_LIBRARY_PATH'
    lp_mod = os.environ.get(lp_key + '_ORIG', None)
    if lp_mod is not None:
        logger.debug("Modfify environment with '%s=%s.'", lp_key, lp_mod)
    else:
        lp_mod = os.environ.get(lp_key, "")
    with TemporaryOSEnviron(env={lp_key: lp_mod}):
        logger.debug("Open %s.", uri)
        if platform.system() == 'Darwin':  # macOS
            logger.debug("On macOS, launch 'open %s'", filepath)
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            if filepath[0] == '/':
                # remove leading slash from path such as /C:/Users/admin/...
                filepath = filepath[1:]
            # convert / to \
            filepath = os.path.abspath(filepath)
            logger.debug("On Windows, launch wth os.startfile('%s')", filepath)
            os.startfile(filepath)
            # direct call of start won't work for directories
            # subprocess.call(('start', filepath))
        else:  # linux variants
            logger.debug("On Linux, launch with Gio.AppInfo.launch_default_for_uri_async('%s')", uri)
            # On Linux, use the Gio.AppInfo mechanism instead of direct xdg-open
            Gio.AppInfo.launch_default_for_uri_async(uri)
            # subprocess.call(('xdg-open', filepath))