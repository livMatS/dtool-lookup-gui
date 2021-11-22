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

import asyncio
import os

from gi.repository import Gio, Gtk

from dtoolcore.utils import get_config_value, write_config_value_to_file, generous_parse_uri, _get_config_dict_from_file
from dtool_lookup_api.core.config import Config
from dtool_lookup_api.core.LookupClient import authenticate

from .authentication_dialog import AuthenticationDialog
from .s3_configuration_dialog import S3ConfigurationDialog


def _is_configured(base_uri):
    if base_uri.scheme == 's3':
        return get_config_value(f'DTOOL_S3_ENDPOINT_{base_uri.netloc}') is not None
    else:
        return False


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/settings_dialog.ui')
class SettingsDialog(Gtk.Window):
    __gtype_name__ = 'DtoolSettingsDialog'

    lookup_url_entry = Gtk.Template.Child()
    token_entry = Gtk.Template.Child()
    authenticator_url_entry = Gtk.Template.Child()
    dependency_keys_entry = Gtk.Template.Child()
    verify_ssl_certificate_switch = Gtk.Template.Child()
    endpoints_list_box = Gtk.Template.Child()

    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)
        self.main_application = parent.main_application
        self.event_loop = parent.event_loop
        self.settings = parent.settings

        self.main_application.settings.settings.bind("dependency-keys",
                                                     self.dependency_keys_entry, 'text',
                                                     Gio.SettingsBindFlags.DEFAULT)

        if Config.lookup_url is not None:
            self.lookup_url_entry.set_text(Config.lookup_url)
        if Config.token is not None:
            self.token_entry.set_text(Config.token)
        if Config.auth_url is not None:
            self.authenticator_url_entry.set_text(Config.auth_url)
        if Config.verify_ssl is not None:
            self.verify_ssl_certificate_switch.set_state(Config.verify_ssl)
        asyncio.create_task(self._refresh_list_of_endpoints())

    async def _refresh_list_of_endpoints(self):
        for child in self.endpoints_list_box.get_children():
            child.destroy()
        base_uris = await self.main_application.lookup_tab.lookup.list_base_uris()
        base_uris = {base_uri['base_uri']: base_uri | {'local': False, 'remote': True} for base_uri in base_uris}

        config_dict = _get_config_dict_from_file()
        for key, value in config_dict.items():
            if key.startswith('DTOOL_S3_ENDPOINT'):
                base_uri = f's3://{key[18:]}'
                if base_uri not in base_uris:
                    base_uris[base_uri] = {'local': True, 'remote': False}
                else:
                    base_uris[base_uri]['local'] = True

        for base_uri, info in base_uris.items():
            parsed_uri = generous_parse_uri(base_uri)
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            hbox.set_margin_top(12)
            hbox.set_margin_bottom(12)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{base_uri}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            if info['local'] and info['remote']:
                label.set_markup('This endpoint is reported by the lookup server and it is configured locally.')
            elif not info['local'] and info['remote']:
                label.set_markup('This endpoint is reported by the lookup server, but it is not configured locally.')
            else:
                label.set_markup('This endpoint is configured locally.')
            vbox.pack_start(label, True, True, 0)
            hbox.pack_start(vbox, True, True, 0)
            button = Gtk.Button(image=Gtk.Image.new_from_icon_name('emblem-system-symbolic', Gtk.IconSize.BUTTON))
            button.connect('clicked', self.on_configure_endpoint_clicked)
            # We currently can only configure S3 endpoints through the GUI
            button.set_sensitive(parsed_uri.scheme == 's3')
            button.base_uri = parsed_uri
            hbox.pack_end(button, False, False, 0)
            row.add(hbox)
            self.endpoints_list_box.add(row)

        # Plus button for adding new endpoints
        row = Gtk.ListBoxRow()
        image = Gtk.Image.new_from_icon_name('list-add-symbolic', Gtk.IconSize.BUTTON)
        image.set_margin_top(20)
        image.set_margin_bottom(20)
        image.set_margin_start(12)
        image.set_margin_end(12)
        row.connect('state-changed', self.on_add_endpoint_state_changed)
        row.add(image)
        self.endpoints_list_box.add(row)

        self.endpoints_list_box.show_all()

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        # Write back configuration
        Config.lookup_url = self.lookup_url_entry.get_text()
        Config.token = self.token_entry.get_text()
        Config.auth_url = self.authenticator_url_entry.get_text()
        Config.verify_ssl = self.verify_ssl_certificate_switch.get_state()

        # Reconnect since settings may have been changed
        asyncio.create_task(self.main_application.lookup_tab.connect())

        # Destroy window
        return False

    @Gtk.Template.Callback()
    def on_renew_token_clicked(self, widget):
        def authenticate(username, password):
            asyncio.create_task(self.retrieve_token(
                self.authenticator_url_entry.get_text(),
                username,
                password))

            # Reconnect since settings may have been changed
            asyncio.create_task(self.main_application.lookup_tab.connect())

        AuthenticationDialog(authenticate, Config.username, Config.password).show()

    async def retrieve_token(self, auth_url, username, password):
        self.main_application.error_bar.hide()
        try:
            token = await authenticate(auth_url, username, password)
        except Exception as e:
            self.main_application.show_error(str(e))
            return
        self.builder.get_object('token-entry').set_text(token)
        await self._refresh_list_of_endpoints()

    def on_configure_endpoint_clicked(self, widget):
        S3ConfigurationDialog(lambda: asyncio.create_task(self._refresh_list_of_endpoints()),
                              widget.base_uri.netloc).show()

    def on_add_endpoint_state_changed(self, widget, state):
        if state == Gtk.StateType.ACTIVE:
            S3ConfigurationDialog(lambda: asyncio.create_task(self._refresh_list_of_endpoints())).show()