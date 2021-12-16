#
# Copyright 2021 Lars Pastewka
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

import os

from gi.repository import Gio


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            f'{os.path.dirname(__file__)}/..', Gio.SettingsSchemaSource.get_default(), False)
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-lookup-gui", False)
        self.settings = Gio.Settings.new_full(schema, None, None)

    @property
    def dependency_keys(self):
        return self.settings.get_string('dependency-keys')

    @property
    def local_base_uris(self):
        return self.settings.get_strv('local-base-uris')

    @local_base_uris.setter
    def local_base_uris(self, value):
        self.settings.set_strv('local-base-uris', value)

settings = Settings()