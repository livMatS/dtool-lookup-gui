#
# Copyright 2021-2022 Johannes Laurin Hörmann
#           2021 Lars Pastewka
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
import argparse
import logging
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '4')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, GdkPixbuf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gio_appinfo_list = Gio.AppInfo.get_all()

# print(app_info_list)

for gio_appinfo in gio_appinfo_list:
    gio_appinfo_dict = {
        'commandline': gio_appinfo.get_commandline(),
        'description': gio_appinfo.get_description(),
        'display_name': gio_appinfo.get_display_name(),
        'executable': gio_appinfo.get_executable(),
        'id': gio_appinfo.get_id(),
        'supported_types': gio_appinfo.get_supported_types(),
    }
    logger.info(gio_appinfo_dict)
# Gio.AppInfo.launch_default_for_uri_async(uri)


class ArgumentDefaultsAndRawDescriptionHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=ArgumentDefaultsAndRawDescriptionHelpFormatter)

parser.add_argument('uri', help='URI to launch')


args = parser.parse_args()

uri = args.uri

scheme = GLib.uri_parse_scheme(uri)
logger.info("URI %s has scheme %s", uri, scheme)


gio_appinfo = Gio.AppInfo.get_default_for_uri_scheme(scheme)
gio_appinfo_dict = {
    'commandline': gio_appinfo.get_commandline(),
    'description': gio_appinfo.get_description(),
    'display_name': gio_appinfo.get_display_name(),
    'executable': gio_appinfo.get_executable(),
    'id': gio_appinfo.get_id(),
    'supported_types': gio_appinfo.get_supported_types(),
}
logger.info(gio_appinfo_dict)

logger.info("Launch default app for %s", uri)
Gio.AppInfo.launch_default_for_uri_async(uri)
