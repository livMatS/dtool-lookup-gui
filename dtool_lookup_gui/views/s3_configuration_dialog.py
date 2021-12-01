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

from gi.repository import Gtk

from dtoolcore.utils import get_config_value, write_config_value_to_file


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/s3_configuration_dialog.ui')
class S3ConfigurationDialog(Gtk.Window):
    __gtype_name__ = 'DtoolS3ConfigurationDialog'

    bucket_entry = Gtk.Template.Child()
    endpoint_url_entry = Gtk.Template.Child()
    access_key_entry = Gtk.Template.Child()
    secret_key_entry = Gtk.Template.Child()
    prefix_entry = Gtk.Template.Child()

    def __init__(self, apply=lambda: None, bucket=None, **kwargs):
        super().__init__(**kwargs)

        if bucket is not None:
            self.bucket_entry.set_text(bucket)
            self.bucket_entry.set_sensitive(False)  # Don't allow edit if we already know the bucket name
            self.endpoint_url_entry.set_text(get_config_value(f'DTOOL_S3_ENDPOINT_{bucket}', default=''))
            self.access_key_entry.set_text(get_config_value(f'DTOOL_S3_ACCESS_KEY_ID_{bucket}', default=''))
            self.secret_key_entry.set_text(get_config_value(f'DTOOL_S3_SECRET_ACCESS_KEY_{bucket}', default=''))
            self.prefix_entry.set_text(get_config_value(f'DTOOL_S3_DATASET_PREFIX', default=''))

        self._apply = apply

    @Gtk.Template.Callback()
    def on_apply_clicked(self, widget):
        bucket = self.bucket_entry.get_text()
        write_config_value_to_file(f'DTOOL_S3_ENDPOINT_{bucket}', self.endpoint_url_entry.get_text())
        write_config_value_to_file(f'DTOOL_S3_ACCESS_KEY_ID_{bucket}', self.access_key_entry.get_text())
        write_config_value_to_file(f'DTOOL_S3_SECRET_ACCESS_KEY_{bucket}', self.secret_key_entry.get_text())
        write_config_value_to_file(f'DTOOL_S3_DATASET_PREFIX', self.prefix_entry.get_text())
        self._apply()
        self.destroy()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, widget):
        self.destroy()
