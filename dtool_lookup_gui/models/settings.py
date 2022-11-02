#
# Copyright 2022 Johannes Laurin Hörmann
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

import logging
import os

from gi.repository import Gio


logger = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.abspath(f'{os.path.dirname(__file__)}/..'), Gio.SettingsSchemaSource.get_default(), False)
        self._schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-lookup-gui", False)
        self.settings = Gio.Settings.new_full(self._schema, None, None)

    def reset(self):
        """Reset Gtk app settings to defaults."""
        keys = self._schema.list_keys()
        for key in keys:
            value = self.settings.get_value(key)
            self.settings.reset(key)
            default = self.settings.get_value(key)
            logger.debug("Reset '%s': '%s' back to default '%s'", key, value, default)

    @property
    def dependency_keys(self):
        return self.settings.get_string('dependency-keys')

    @property
    def local_base_uris(self):
        return self.settings.get_strv('local-base-uris')

    @local_base_uris.setter
    def local_base_uris(self, value):
        self.settings.set_strv('local-base-uris', value)

    @property
    def item_download_directory(self):
        return self.settings.get_string('item-download-directory')

    @item_download_directory.setter
    def item_download_directory(self, value):
        self.settings.set_string('item-download-directory', value)

    @property
    def choose_item_download_directory(self):
        return self.settings.get_boolean('choose-item-download-directory')

    @choose_item_download_directory.setter
    def choose_item_download_directory(self, value):
        self.settings.set_boolean('choose-item-download-directory', value)

    @property
    def open_downloaded_item(self):
        return self.settings.get_boolean('open-downloaded-item')

    @open_downloaded_item.setter
    def open_downloaded_item(self, value):
        self.settings.set_boolean('open-downloaded-item', value)


settings = Settings()
