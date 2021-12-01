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


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/smb_configuration_dialog.ui')
class SMBConfigurationDialog(Gtk.Window):
    __gtype_name__ = 'DtoolSMBConfigurationDialog'

    name_entry = Gtk.Template.Child()
    server_name_entry = Gtk.Template.Child()
    server_port_entry = Gtk.Template.Child()
    service_name_entry = Gtk.Template.Child()
    path_entry = Gtk.Template.Child()
    domain_entry = Gtk.Template.Child()
    username_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()

    def __init__(self, apply=lambda: None, name=None, **kwargs):
        super().__init__(**kwargs)

        if name is not None:
            self.name_entry.set_text(name)
            self.name_entry.set_sensitive(False)  # Don't allow edit if we already know the name name
            self.server_name_entry.set_text(get_config_value(f'DTOOL_SMB_SERVER_NAME_{name}', default=''))
            self.server_port_entry.set_text(str(get_config_value(f'DTOOL_SMB_SERVER_PORT_{name}', default='445')))
            self.service_name_entry.set_text(get_config_value(f'DTOOL_SMB_SERVICE_NAME_{name}', default=''))
            self.path_entry.set_text(get_config_value(f'DTOOL_SMB_PATH_{name}', default=''))
            self.domain_entry.set_text(get_config_value(f'DTOOL_SMB_DOMAIN_{name}', default=''))
            self.username_entry.set_text(get_config_value(f'DTOOL_SMB_USERNAME_{name}', default=''))
            self.password_entry.set_text(get_config_value(f'DTOOL_SMB_PASSWORD_{name}', default=''))

        self._apply = apply

    @Gtk.Template.Callback()
    def on_apply_clicked(self, widget):
        name = self.name_entry.get_text()
        write_config_value_to_file(f'DTOOL_SMB_SERVER_NAME_{name}', self.server_name_entry.get_text())
        write_config_value_to_file(f'DTOOL_SMB_SERVER_PORT_{name}', int(self.server_port_entry.get_text()))
        write_config_value_to_file(f'DTOOL_SMB_SERVICE_NAME_{name}', self.service_name_entry.get_text())
        write_config_value_to_file(f'DTOOL_SMB_PATH_{name}', self.path_entry.get_text())
        write_config_value_to_file(f'DTOOL_SMB_DOMAIN_{name}', self.domain_entry.get_text())
        write_config_value_to_file(f'DTOOL_SMB_USERNAME_{name}', self.username_entry.get_text())
        write_config_value_to_file(f'DTOOL_SMB_PASSWORD_{name}', self.password_entry.get_text())
        self._apply()
        self.destroy()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, widget):
        self.destroy()
